import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;

import uk.ac.cam.ch.wwmm.chemicaltagger.POSContainer;
import uk.ac.cam.ch.wwmm.chemicaltagger.ChemistryPOSTagger;
import uk.ac.cam.ch.wwmm.chemicaltagger.ChemistrySentenceParser;
import uk.ac.cam.ch.wwmm.chemicaltagger.Utils;
import nu.xom.Document;

import py4j.GatewayServer;



public class ChemicalTaggerApp{

  public void chemtag(String text, String outfile) throws IOException {

    System.out.println(outfile);
    // Calling ChemistryPOSTagger
    POSContainer posContainer = ChemistryPOSTagger.getDefaultInstance().runTaggers(text);

    // Returns a string of TAG TOKEN format (e.g.: DT The NN cat VB sat IN on DT the NN matt)
    // Call ChemistrySentenceParser either by passing the POSContainer or by InputStream
    ChemistrySentenceParser chemistrySentenceParser = new ChemistrySentenceParser(posContainer);

    // Create a parseTree of the tagged input
    chemistrySentenceParser.parseTags();

    // Return an XMLDoc
    Document doc = chemistrySentenceParser.makeXMLDocument();

    Utils.writeXMLToFile(doc, outfile);

  }

  public static void main(String[] args) {
    ChemicalTaggerApp app = new ChemicalTaggerApp();
    // app を gateway.entry_point に設定
    GatewayServer server = new GatewayServer(app);
    server.start();
    System.out.println("Gateway Server Started");
  }

}
