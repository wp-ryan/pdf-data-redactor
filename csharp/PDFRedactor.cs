using System;
using System.IO;
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
    }

    // Helper class for loading config that supports both string and array for Find field
    public class ConfigReplacementRule
    {
        private object _find;
        
        public object Find 
        { 
            get => _find;
            set => _find = value;
        }
        public string Replace { get; set; }
        public bool Regex { get; set; }

        // Helper method to get find patterns as a list
        public List<string> GetFindPatterns()
        {
            if (_find is string stringValue)
                return new List<string> { stringValue };
            else if (_find is Newtonsoft.Json.Linq.JArray arrayValue)
                return arrayValue.ToObject<List<string>>();
            else
                return new List<string>();
        }
    }

    public class Config
    {
        public List<ConfigReplacementRule> Replacements { get; set; }
    }

    class PDFRedactor
    {
        private List<ReplacementRule> replacements = new List<ReplacementRule>();

        public void AddReplacement(string find, string replace, bool isRegex = false)
        {
            replacements.Add(new ReplacementRule 
            { 
                Find = find, 
                Replace = replace, 
                Regex = isRegex 
            });
        }

        public void LoadConfig(string configPath)
        {
            var json = File.ReadAllText(configPath);
            var config = JsonConvert.DeserializeObject<Config>(json);
            
            foreach (var configRule in config.Replacements)
            {
                var findPatterns = configRule.GetFindPatterns();
                foreach (var pattern in findPatterns)
                {
                    replacements.Add(new ReplacementRule
                    {
                        Find = pattern,
                        Replace = configRule.Replace,
                        Regex = configRule.Regex
                    });
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
                    result = Regex.Replace(result, rule.Find, rule.Replace);
                }
                else
                {
                    result = result.Replace(rule.Find, rule.Replace);
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
