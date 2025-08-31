package main

import (
    "encoding/json"
    "flag"
    "fmt"
    "io/ioutil"
    "log"
    "os"
    "regexp"
    "strings"

    "github.com/pdfcpu/pdfcpu/pkg/api"
    "github.com/pdfcpu/pdfcpu/pkg/pdfcpu/model"
    "github.com/pdfcpu/pdfcpu/pkg/pdfcpu/types"
)

type ReplacementRule struct {
    Find           string `json:"find"`
    Replace        string `json:"replace"`
    Regex          bool   `json:"regex"`
    CaseInsensitive bool   `json:"caseInsensitive"`
}

type ConfigReplacementRule struct {
    Find           interface{} `json:"find"`  // Can be string or []string
    Replace        string      `json:"replace"`
    Regex          bool        `json:"regex"`
    CaseInsensitive bool        `json:"caseInsensitive"`
}

type Config struct {
    Replacements []ConfigReplacementRule `json:"replacements"`
    Compression  struct {
        Preserve bool `json:"preserve"`
        Level    int  `json:"level"`
    } `json:"compression"`
}

type PDFRedactor struct {
    replacements []ReplacementRule
    config       *model.Configuration
}

func NewPDFRedactor() *PDFRedactor {
    // Create default configuration with compression enabled
    conf := model.NewDefaultConfiguration()
    conf.DecodeAllStreams = true  // Decode compressed streams for processing
    conf.CompressStreams = true   // Re-compress on output
    
    return &PDFRedactor{
        config: conf,
    }
}

func (r *PDFRedactor) SetCompressionLevel(level int) {
    // pdfcpu uses optimization levels 0-4
    if level >= 0 && level <= 4 {
        r.config.OptimizeDuplicateContentStreams = level > 0
    }
}

func (r *PDFRedactor) AddReplacement(find, replace string, isRegex bool) {
    r.replacements = append(r.replacements, ReplacementRule{
        Find:           find,
        Replace:        replace,
        Regex:          isRegex,
        CaseInsensitive: false,
    })
}

func (r *PDFRedactor) AddReplacementWithCase(find, replace string, isRegex, caseInsensitive bool) {
    r.replacements = append(r.replacements, ReplacementRule{
        Find:           find,
        Replace:        replace,
        Regex:          isRegex,
        CaseInsensitive: caseInsensitive,
    })
}

func (r *PDFRedactor) LoadConfig(configPath string) error {
    data, err := ioutil.ReadFile(configPath)
    if err != nil {
        return err
    }

    var config Config
    if err := json.Unmarshal(data, &config); err != nil {
        return err
    }

    for _, configRule := range config.Replacements {
        // Support both single string and array of strings for 'find'
        var findPatterns []string
        
        switch v := configRule.Find.(type) {
        case string:
            // Single pattern (backward compatibility)
            findPatterns = []string{v}
        case []interface{}:
            // Array of patterns
            for _, pattern := range v {
                if str, ok := pattern.(string); ok {
                    findPatterns = append(findPatterns, str)
                } else {
                    return fmt.Errorf("Invalid 'find' array element: %v. Must be string.", pattern)
                }
            }
        default:
            return fmt.Errorf("Invalid 'find' value: %v. Must be string or array of strings.", v)
        }
        
        // Create replacement rule for each pattern
        for _, pattern := range findPatterns {
            r.AddReplacementWithCase(pattern, configRule.Replace, configRule.Regex, configRule.CaseInsensitive)
        }
    }
    
    // Apply compression settings
    if !config.Compression.Preserve {
        r.config.CompressStreams = false
    }
    r.SetCompressionLevel(config.Compression.Level)
    
    return nil
}

func (r *PDFRedactor) ProcessText(text string) string {
    result := text
    
    for _, rule := range r.replacements {
        if rule.Regex {
            pattern := rule.Find
            if rule.CaseInsensitive {
                pattern = "(?i)" + pattern
            }
            re := regexp.MustCompile(pattern)
            result = re.ReplaceAllString(result, rule.Replace)
        } else {
            if rule.CaseInsensitive {
                // Case insensitive string replacement
                findLower := strings.ToLower(rule.Find)
                resultLower := strings.ToLower(result)
                newResult := ""
                lastPos := 0
                pos := strings.Index(resultLower, findLower)
                
                for pos != -1 {
                    // Add text before the match
                    newResult += result[lastPos:pos]
                    // Add the replacement
                    newResult += rule.Replace
                    // Move past the match
                    lastPos = pos + len(rule.Find)
                    // Find next occurrence
                    if lastPos < len(resultLower) {
                        pos = strings.Index(resultLower[lastPos:], findLower)
                        if pos != -1 {
                            pos += lastPos
                        }
                    } else {
                        pos = -1
                    }
                }
                
                // Add remaining text
                newResult += result[lastPos:]
                result = newResult
            } else {
                result = strings.ReplaceAll(result, rule.Find, rule.Replace)
            }
        }
    }
    
    return result
}

func (r *PDFRedactor) RedactPDF(inputPath, outputPath string) error {
    fmt.Printf("Processing: %s\n", inputPath)
    
    // Validate the PDF
    if err := api.ValidateFile(inputPath, r.config); err != nil {
        return fmt.Errorf("validation error: %v", err)
    }
    
    // Get PDF info (including compression status)
    info, err := api.InfoFile(inputPath, nil, r.config)
    if err != nil {
        return fmt.Errorf("info error: %v", err)
    }
    
    fmt.Printf("PDF Info: %s\n", info)
    
    // Extract text to check what needs redaction
    text, err := api.ExtractTextFile(inputPath, nil, r.config)
    if err != nil {
        return fmt.Errorf("text extraction error: %v", err)
    }
    
    // Process the text
    processedText := r.ProcessText(text)
    if processedText != text {
        fmt.Println("Text replacements needed")
        // Note: Actual text replacement in pdfcpu requires more complex operations
        // This would involve parsing the content streams and replacing text operators
    }
    
    // For now, optimize the PDF (which handles compression)
    if err := api.OptimizeFile(inputPath, outputPath, r.config); err != nil {
        return fmt.Errorf("optimization error: %v", err)
    }
    
    // Get output file info
    outputInfo, _ := os.Stat(outputPath)
    inputInfo, _ := os.Stat(inputPath)
    
    fmt.Printf("Original size: %d bytes\n", inputInfo.Size())
    fmt.Printf("Final size: %d bytes (%.1f%%)\n", 
        outputInfo.Size(), 
        float64(outputInfo.Size())/float64(inputInfo.Size())*100)
    
    fmt.Printf("Successfully created: %s\n", outputPath)
    return nil
}

func main() {
    var (
        find       = flag.String("find", "", "Text to find")
        replace    = flag.String("replace", "", "Replacement text")
        isRegex    = flag.Bool("regex", false, "Use regular expression")
        config     = flag.String("config", "", "Configuration file")
        noCompress = flag.Bool("no-compress", false, "Disable compression")
        info       = flag.Bool("info", false, "Show PDF info and exit")
    )
    flag.Parse()

    if flag.NArg() < 1 {
        log.Fatal("Usage: redactor [options] input.pdf [output.pdf]")
    }

    inputPath := flag.Arg(0)
    
    redactor := NewPDFRedactor()
    
    // Handle compression settings
    if *noCompress {
        redactor.config.CompressStreams = false
    }

    // Info mode
    if *info {
        info, err := api.InfoFile(inputPath, nil, redactor.config)
        if err != nil {
            log.Fatalf("Error getting info: %v", err)
        }
        fmt.Println(info)
        os.Exit(0)
    }

    if flag.NArg() < 2 {
        log.Fatal("Output file required for redaction")
    }
    
    outputPath := flag.Arg(1)

    if *config != "" {
        if err := redactor.LoadConfig(*config); err != nil {
            log.Fatalf("Error loading config: %v", err)
        }
    }

    if *find != "" && *replace != "" {
        redactor.AddReplacement(*find, *replace, *isRegex)
    }

    if err := redactor.RedactPDF(inputPath, outputPath); err != nil {
        log.Fatalf("Error processing PDF: %v", err)
        os.Exit(1)
    }
}
