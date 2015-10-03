
import java.io.*;
import java.util.*;
import java.util.Arrays;

import edu.stanford.nlp.dcoref.CorefChain;
import edu.stanford.nlp.dcoref.CorefCoreAnnotations;
import edu.stanford.nlp.io.*;
import edu.stanford.nlp.ling.*;
import edu.stanford.nlp.pipeline.*;
import edu.stanford.nlp.ling.CoreAnnotations.*;
import edu.stanford.nlp.trees.TreeCoreAnnotations.*;
import edu.stanford.nlp.semgraph.SemanticGraph;
import edu.stanford.nlp.semgraph.*;
import edu.stanford.nlp.semgraph.SemanticGraphCoreAnnotations;
import edu.stanford.nlp.trees.*;
import edu.stanford.nlp.util.*;

public class DependencyParser {

  String VERSION = "0.01";

  private static StanfordCoreNLP pipeline;

  /** Usage: java -cp "*" StanfordCoreNlpDemo [inputFile [outputTextFile [outputXmlFile]]] */
  public static void main(String[] args) throws IOException {

   
  	Properties props = new Properties();
  	props.setProperty("annotators", "tokenize, ssplit, pos, lemma, ner, depparse");
    props.put("ssplit.newlineIsSentenceBreak", "always");

  	pipeline = new StanfordCoreNLP(props);


    File[] files = new File(args[0]).listFiles();
    iterateFiles(files);
  }

  public static void iterateFiles(File[] files) throws IOException{

    if(files.length == 0)
      return;

    String prefix = files[0].getPath().split("\\.")[0];

    File f = new File(prefix+"_out_dependencies.csv");
    if (f.exists())
      return;

    PrintWriter dependOut = new PrintWriter(prefix+"_out_dependencies.csv");
    PrintWriter posOut = new PrintWriter(prefix+"_out_pos.csv");

    for (File file : files) {
        if (file.isDirectory()) {
            iterateFiles(file.listFiles());
        } else {
            String path = file.getPath();
            if(path.endsWith(".txt"))
              parseFile(path, dependOut, posOut);
        }
    }

    IOUtils.closeIgnoringExceptions(dependOut);
    IOUtils.closeIgnoringExceptions(posOut);
  }

  private static void parseFile(String filePath, PrintWriter dependOut, PrintWriter posOut) throws IOException{

    System.out.println(filePath);

    String text = readFile(filePath);

    String path = filePath.split(".txt")[0];
    String[] pathArr = path.split("/");
    path = pathArr[pathArr.length - 1];
    Annotation document = new Annotation(text);

    pipeline.annotate(document);

    List<CoreMap> sentences = document.get(SentencesAnnotation.class);


    for(int i = 0; i <sentences.size()-1; i++){
        CoreMap sentence = sentences.get(i);
    
        List<CoreLabel> tokens = sentence.get(TokensAnnotation.class);
        
        for(int j = 0; j < tokens.size()-1; j++){
          CoreLabel token = tokens.get(j);

          String  word = token.get(TextAnnotation.class);

          String ne = token.get(NamedEntityTagAnnotation.class);
          
          String pos = token.get(PartOfSpeechAnnotation.class);

          int idx = token.index();

          posOut.println(path+"^"+i+"^"+idx+"^"+word+"^"+pos+"^"+ne);

        }

        Tree tree = sentence.get(TreeAnnotation.class);

        SemanticGraph dependencies = sentence.get(SemanticGraphCoreAnnotations.CollapsedCCProcessedDependenciesAnnotation.class);
                
        IndexedWord root = dependencies.getFirstRoot();
        dependOut.println(path+"\t"+i+"\troot\tROOT\t0\t"+root.word()+"\t"+root.index());
        for (SemanticGraphEdge edge : dependencies.edgeListSorted()) {
          String reln = edge.getRelation().toString();

          int govIdx = (edge.getSource()).index();
          String gov = (edge.getSource()).word();
          String dep = (edge.getTarget()).word();
          int depIdx = (edge.getTarget()).index();

          dependOut.println(path+"\t"+i+"\t"+reln+"\t"+gov+"\t"+govIdx+"\t"+dep+"\t"+depIdx);
        }
    }
  }

  private static String readFile(String fileName) throws IOException{
      
      try {
          BufferedReader br = new BufferedReader(new FileReader(fileName));
          StringBuilder sb = new StringBuilder();
          String line = br.readLine();

          while (line != null) {
              sb.append(line);
              sb.append(System.lineSeparator());
              line = br.readLine();
          }
          String everything = sb.toString();
          return everything;

      } 
      catch(IOException e){
          System.out.println("Exception !!!!");
      }
      return "";
  }
}