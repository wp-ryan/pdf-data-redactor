using System;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Collections.Generic;
using PdfSharp.Pdf;
using PdfSharp.Pdf.IO;
using PdfSharp.Pdf.Content;
using PdfSharp.Pdf.Content.Objects;
using CommandLine;
using Newtonsoft.Json;

namespace PDFRedactor
{
    public class Options
    {
        [Value(0, HelpText = "Input PDF file")]
        public string Input { get; set; }

        [Value(1, HelpText = "Output PDF file")]
        public string Output { get; set; }

        [Option('f', "find", HelpText = "Text to find")]
        public string Find { get; set; }

        [Option('r', "replace", HelpText = "Replacement text")]
        public string Replace { get; set; }

        [Option("regex", HelpText = "Use regular expression matching")]
        public bool IsRegex { get; set; }

        [Option('c', "config", HelpText = "Configuration file")]
        public string Config { get; set; }
    }

    public class ReplacementRule
    {
        public string Find { get; set; }
        public string Replace { get; set; }
        public bool Regex { get; set; }
        public bool CaseInsensitive { get; set; }
    }

    public class ConfigReplacementRule
    {
        public object Find { get; set; }  // Can be string or string[]
        public string Replace { get; set; }
        public bool Regex { get; set; }
        public bool CaseInsensitive { get; set; }
    }

    public class Config
    {
        public List<ConfigReplacementRule> Replacements { get; set; }
    }

    class PDFRedactor
    {
        private List<ReplacementRule> replacements = new List<ReplacementRule>();

        public void AddReplacement(string find, string replace, bool isRegex = false, bool caseInsensitive = false)
        {
            replacements.Add(new ReplacementRule 
            { 
                Find = find, 
                Replace = replace, 
                Regex = isRegex,
                CaseInsensitive = caseInsensitive
            });
        }

        public void LoadConfig(string configPath)
        {
            var json = File.ReadAllText(configPath);
            var config = JsonConvert.DeserializeObject<Config>(json);
            
            foreach (var configRule in config.Replacements)
            {
                // Support both single string and array of strings for 'find'
                List<string> findPatterns = new List<string>();
                
                if (configRule.Find is string singlePattern)
                {
                    // Single pattern (backward compatibility)
                    findPatterns.Add(singlePattern);
                }
                else if (configRule.Find is Newtonsoft.Json.Linq.JArray arrayPatterns)
                {
                    // Array of patterns
                    foreach (var pattern in arrayPatterns)
                    {
                        findPatterns.Add(pattern.ToString());
                    }
                }
                else
                {
                    throw new ArgumentException($"Invalid 'find' value: {configRule.Find}. Must be string or array of strings.");
                }
                
                // Create replacement rule for each pattern
                foreach (var pattern in findPatterns)
                {
                    AddReplacement(pattern, configRule.Replace, configRule.Regex, configRule.CaseInsensitive);
                }
            }
        }

        public string ProcessText(string text)
        {
            var result = text;
            
            foreach (var rule in replacements)
            {
                if (rule.Regex)
                {
                    var options = rule.CaseInsensitive ? RegexOptions.IgnoreCase : RegexOptions.None;
                    result = Regex.Replace(result, rule.Find, rule.Replace, options);
                }
                else
                {
                    if (rule.CaseInsensitive)
                    {
                        // Case insensitive string replacement
                        var comparison = StringComparison.OrdinalIgnoreCase;
                        var findLength = rule.Find.Length;
                        var sb = new StringBuilder();
                        int lastPos = 0;
                        int pos = result.IndexOf(rule.Find, comparison);
                        
                        while (pos != -1)
                        {
                            // Add text before the match
                            sb.Append(result.Substring(lastPos, pos - lastPos));
                            // Add the replacement
                            sb.Append(rule.Replace);
                            // Move past the match
                            lastPos = pos + findLength;
                            // Find next occurrence
                            pos = result.IndexOf(rule.Find, lastPos, comparison);
                        }
                        
                        // Add remaining text
                        sb.Append(result.Substring(lastPos));
                        result = sb.ToString();
                    }
                    else
                    {
                        result = result.Replace(rule.Find, rule.Replace);
                    }
                }
            }
            
            return result;
        }

        public bool RedactPdf(string inputPath, string outputPath)
        {
            try
            {
                Console.WriteLine($"Processing: {inputPath}");
                
                // Open the PDF
                using (var document = PdfReader.Open(inputPath, PdfDocumentOpenMode.Modify))
                {
                    // Process each page
                    foreach (var page in document.Pages)
                    {
                        // Extract and process content
                        // Note: PDFsharp has limitations in text extraction/replacement
                        // This is a simplified example
                    }
                    
                    // Save the document
                    document.Save(outputPath);
                }
                
                Console.WriteLine($"Successfully created: {outputPath}");
                return true;
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"Error: {ex.Message}");
                return false;
            }
        }

        static void Main(string[] args)
        {
            Parser.Default.ParseArguments<Options>(args)
                .WithParsed<Options>(opts =>
                {
                    var redactor = new PDFRedactor();
                    
                    if (!string.IsNullOrEmpty(opts.Config))
                    {
                        redactor.LoadConfig(opts.Config);
                    }
                    
                    if (!string.IsNullOrEmpty(opts.Find) && !string.IsNullOrEmpty(opts.Replace))
                    {
                        redactor.AddReplacement(opts.Find, opts.Replace, opts.IsRegex);
                    }
                    
                    var success = redactor.RedactPdf(opts.Input, opts.Output);
                    Environment.Exit(success ? 0 : 1);
                });
        }
    }
}
