
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

    for (File file : files) {
        if (file.isDirectory()) {
            iterateFiles(file.listFiles());
        } else {
            String path = file.getPath();
            if(path.endsWith(".txt"))
              parseFile(path);
        }
    }

  }

  private static void parseFile(String filePath) throws IOException{


    String path = filePath.split(".txt")[0];
    String[] pathArr = path.split("/");
    path = pathArr[pathArr.length - 1];

    File dependOut = new File("data/deps/"+path+".deps");

    System.out.println(filePath);

    String text = readFile(filePath);    Annotation document = new Annotation(text);

    pipeline.annotate(document);

    CoNLLOutputter.conllPrint(document, new FileOutputStream(dependOut));
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