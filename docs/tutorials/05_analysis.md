
The Analysis module of Pandora allows the user to calculate basic statistics generated from the data stored during a simulation. This tutorial will define how to use it using the C++ interface of the framework. These analysis generate a set of csv files (Comma Separated Values) that can be loaded from any spreadsheet application (like LibreOffice Calc), as well as from several statistical packages (like R).

We will generate a basic dataset, and will try to load it afterwards.
First of all let's create the simulation. Follow the tutorial (Link 01_GETTING_STARTED_PYPANDORA.txt) and execute the simulation. It will create a folder called 'data' with the files 'results.h5' and 'agents-0.abm' in it. These files contain the data from rasters and agents collected during each time step.

Create a folder called 05_src inside examples:

- PANDORA_ROOT
	- examples
		- 05_src

And define a new file 'main.cxx', where we will program the analysis. In order to do that, we need to load it into an instance of the class SimulationRecord:

#include <SimulationRecord.hxx>

int main(int argc, char *argv[])
{
	Engine::SimulationRecord simRecord( 1, false);
	simRecord.loadHDF5("data/results.h5", true, true);
}


These lines create a SimulationRecord and loads the file 'data/results.h5'. The parameters of the constructor are the resolution at which data must be loaded (we have specified to load every time step, but you could also define a resolution of 10, thus loading a time step every ten). The second parameter specifies that this SimulationRecord will not be displayed on a GUI (like Cassandra), thus showing the progress of the task in command line.

The method loadHDF5 has three parameters.  The first one is the file to be loaded. If the folder generated by the simulation is in another path please modify this parameter. The two other parameters allow the user to specify if agents and rasters must be loaded (flag set to true) or not (flag set to false).

Once that data is loaded, we will create a set of tools to analyze the agents, as well as the values of the rasters. This is done using classes such as GlobalAgentStats and GlobalRasterStats. They are useful to gather global statistics of the results (i.e. mean values of agent properties, sum of raster values, etc). There are other analysis, like AgentHistogram or Individual Stats that can be used to collect additional information about the output of our simulations (you can even create your own analysis, inheriting from Output base class):

PostProcess::GlobalAgentStats agentResults;	
PostProcess::GlobalRasterStats rasterResults;

We will add several analysis to both of them. Each analysis is a different class, and has a different set of parameters, for example:

agentResults.addAnalysis(std::shared_ptr<PostProcess::AgentNum> (new PostProcess::AgentNum()));
agentResults.addAnalysis(std::shared_ptr<PostProcess::AgentMean> (new PostProcess::AgentMean("x")));
agentResults.addAnalysis(std::shared_ptr<PostProcess::AgentMean> (new PostProcess::AgentMean("y")));
agentResults.addAnalysis(std::shared_ptr<PostProcess::AgentMean> (new PostProcess::AgentMean("resources")));
agentResults.addAnalysis(std::shared_ptr<PostProcess::AgentSum> (new PostProcess::AgentSum("resources")));

The first analysis stores the number of agents for each time step. The second, third and fourth ones compute the mean of each variable amongst the entire set of agents. The fifth analysis calculates the sum of ressource values gathered by the agents. 
(TODO and finally the last analysis generate a georeferenced file (Shapefile http://www.esri.com/library/whitepapers/pdfs/shapefile.pdf) that can be loaded by any GIS software.)

Regarding rasters, given the fact that each instance of GlobalRasterResults is defined for a raster, we can calculate the Mean and Sum of values:

rasterResults.addAnalysis(std::shared_ptr<PostProcess::RasterMean> (new PostProcess::RasterMean()));
rasterResults.addAnalysis(std::shared_ptr<PostProcess::RasterSum> (new PostProcess::RasterSum()));

Finally, we will need to add these classes in the include section:

#include <analysis/GlobalAgentStats.hxx>
#include <analysis/GlobalRasterStats.hxx>
#include <analysis/AgentMean.hxx>
#include <analysis/AgentSum.hxx>
#include <analysis/RasterMean.hxx>
#include <analysis/RasterSum.hxx>
#include <analysis/AgentNum.hxx>

and apply the results:

agentResults.apply(simRecord, "agents.csv", "MyAgent");
rasterResults.apply(simRecord, "rasters.csv", "resources");

As you can see the method apply receives 3 parameters: the SimulationRecord instance where data was loaded, the output CSV filename and the type of agent or raster name to be analysed. In this way you could apply the same analysis to different types of agents (or diferent rasters), storing the information on CSVs files (to compile and execute the example you can use the scons file located in $PANDORA_ROOT/doc/tutorials/05_src/)

