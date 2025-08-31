import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.pdmodel.PDPage;
import org.apache.pdfbox.text.PDFTextStripper;
import org.apache.pdfbox.contentstream.PDFStreamEngine;
import org.apache.pdfbox.contentstream.operator.Operator;
import org.apache.pdfbox.cos.COSName;
import org.apache.pdfbox.pdmodel.PDPageContentStream;
import org.apache.pdfbox.pdmodel.common.PDRectangle;

import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;

import java.io.*;
import java.util.*;
import java.util.regex.Pattern;
import java.util.regex.Matcher;

public class PDFRedactor {
    
    private List<ReplacementRule> replacements = new ArrayList<>();
    
    static class ReplacementRule {
        String find;
        String replace;
        boolean regex;
        boolean caseInsensitive;
        
        ReplacementRule(String find, String replace, boolean regex) {
            this.find = find;
            this.replace = replace;
            this.regex = regex;
            this.caseInsensitive = false;
        }
        
        ReplacementRule(String find, String replace, boolean regex, boolean caseInsensitive) {
            this.find = find;
            this.replace = replace;
            this.regex = regex;
            this.caseInsensitive = caseInsensitive;
        }
    }
    
    static class Config {
        List<ReplacementRule> replacements;
        CompressionSettings compression;
        
        static class CompressionSettings {
            boolean preserve = true;
            int level = 9;
        }
    }
    
    public void addReplacement(String find, String replace, boolean isRegex) {
        replacements.add(new ReplacementRule(find, replace, isRegex));
    }
    
    public void addReplacement(String find, String replace, boolean isRegex, boolean caseInsensitive) {
        replacements.add(new ReplacementRule(find, replace, isRegex, caseInsensitive));
    }
    
    public void loadConfig(String configPath) throws IOException {
        Gson gson = new Gson();
        try (Reader reader = new FileReader(configPath)) {
            // Parse as JsonObject to handle flexible 'find' field
            com.google.gson.JsonObject jsonConfig = gson.fromJson(reader, com.google.gson.JsonObject.class);
            
            if (jsonConfig.has("replacements")) {
                com.google.gson.JsonArray replacementsArray = jsonConfig.getAsJsonArray("replacements");
                
                for (com.google.gson.JsonElement element : replacementsArray) {
                    com.google.gson.JsonObject rule = element.getAsJsonObject();
                    
                    // Support both single string and array of strings for 'find'
                    String[] findPatterns;
                    com.google.gson.JsonElement findElement = rule.get("find");
                    
                    if (findElement.isJsonArray()) {
                        // Array of patterns
                        com.google.gson.JsonArray findArray = findElement.getAsJsonArray();
                        findPatterns = new String[findArray.size()];
                        for (int i = 0; i < findArray.size(); i++) {
                            findPatterns[i] = findArray.get(i).getAsString();
                        }
                    } else {
                        // Single pattern (backward compatibility)
                        findPatterns = new String[]{findElement.getAsString()};
                    }
                    
                    String replace = rule.get("replace").getAsString();
                    boolean regex = rule.has("regex") ? rule.get("regex").getAsBoolean() : false;
                    boolean caseInsensitive = rule.has("caseInsensitive") ? rule.get("caseInsensitive").getAsBoolean() : false;
                    
                    // Create replacement rule for each pattern
                    for (String pattern : findPatterns) {
                        addReplacement(pattern, replace, regex, caseInsensitive);
                    }
                }
            }
        }
    }
    
    public String processText(String text) {
        String result = text;
        
        for (ReplacementRule rule : replacements) {
            if (rule.regex) {
                if (rule.caseInsensitive) {
                    Pattern pattern = Pattern.compile(rule.find, Pattern.CASE_INSENSITIVE);
                    result = pattern.matcher(result).replaceAll(rule.replace);
                } else {
                    result = result.replaceAll(rule.find, rule.replace);
                }
            } else {
                if (rule.caseInsensitive) {
                    // Case insensitive string replacement
                    String findLower = rule.find.toLowerCase();
                    StringBuilder newResult = new StringBuilder();
                    int lastPos = 0;
                    int pos = result.toLowerCase().indexOf(findLower);
                    
                    while (pos != -1) {
                        // Add text before the match
                        newResult.append(result.substring(lastPos, pos));
                        // Add the replacement
                        newResult.append(rule.replace);
                        // Move past the match
                        lastPos = pos + rule.find.length();
                        // Find next occurrence
                        pos = result.toLowerCase().indexOf(findLower, lastPos);
                    }
                    
                    // Add remaining text
                    newResult.append(result.substring(lastPos));
                    result = newResult.toString();
                } else {
                    result = result.replace(rule.find, rule.replace);
                }
            }
        }
        
        return result;
    }
    
    public void redactPDF(String inputPath, String outputPath) throws IOException {
        System.out.println("Processing: " + inputPath);
        
        try (PDDocument document = PDDocument.load(new File(inputPath))) {
            
            // PDFBox automatically handles decompression when loading
            // and recompression when saving
            
            // Check if document is encrypted
            if (document.isEncrypted()) {
                System.err.println("Warning: Document is encrypted");
            }
            
            // Extract text for processing
            PDFTextStripper stripper = new PDFTextStripper();
            String fullText = stripper.getText(document);
            
            // Check what needs to be replaced
            String processedText = processText(fullText);
            
            if (!processedText.equals(fullText)) {
                System.out.println("Text replacements needed");
                // Note: Actual text replacement in PDFBox requires more complex
                // content stream manipulation
            }
            
            // Get file sizes for comparison
            File inputFile = new File(inputPath);
            long originalSize = inputFile.length();
            
            // Save the document (PDFBox handles compression automatically)
            document.save(outputPath);
            
            File outputFile = new File(outputPath);
            long finalSize = outputFile.length();
            
            System.out.printf("Original size: %,d bytes%n", originalSize);
            System.out.printf("Final size: %,d bytes (%.1f%%)%n", 
                finalSize, 
                (double)finalSize / originalSize * 100);
            
            System.out.println("Successfully created: " + outputPath);
        }
    }
    
    public static void main(String[] args) {
        // Command line parsing would go here
        // For brevity, showing basic usage
        
        if (args.length < 2) {
            System.err.println("Usage: java PDFRedactor input.pdf output.pdf");
            System.exit(1);
        }
        
        PDFRedactor redactor = new PDFRedactor();
        
        // Example: Add a simple replacement
        redactor.addReplacement("confidential", "[REDACTED]", false);
        
        try {
            redactor.redactPDF(args[0], args[1]);
        } catch (IOException e) {
            System.err.println("Error: " + e.getMessage());
            System.exit(1);
        }
    }
}
