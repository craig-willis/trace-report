import graphviz  
from jinja2 import Template
import urllib.parse
from rdflib import Graph
from pprint import pprint

urllib.parse.uses_relative.append('arcp')
urllib.parse.uses_netloc.append('arcp')


class TROReport:
    graph = None
    dot = None
    tro = {}

    def parse(self, location):
        self.graph = Graph()
        self.graph.parse(location=location, format="json-ld")

        self.dot = graphviz.Digraph('TRO')  
        self.dot.graph_attr['rankdir'] = 'LR'  


        self.get_tro_info()
        self.get_trs_info()
        self.get_trp_info()
        self.get_arrangements()
        self.get_artifacts()        
        self.get_trs_capabilities()

    def get_tro_info(self):
        # Name, description, createdBy, and createdDate were added
        tro_info_qry = """
        SELECT DISTINCT ?tro ?name ?description ?createdBy ?createdDate
        WHERE {
            ?tro    rdf:type    trov:TransparentResearchObject .
            ?tro    trov:name ?name .
            ?tro    trov:description ?description .
            ?tro    trov:createdBy ?createdBy .
            ?tro    trov:createdDate ?createdDate .
        }
        """
        qres = self.graph.query(tro_info_qry)
        for row in qres:
            self.tro = {
                "id": str(row.tro),
                "name": str(row.name),
                "description": str(row.description),
                "createdBy": str(row.createdBy),
                "createdDate": str(row.createdDate)
            }

    def get_arrangements(self):
        # Get the list of arrangements
        # TODO: Comment should just be name
        arrangement_qry = """
        SELECT DISTINCT ?arrangement ?name
        WHERE {
            ?arrangement rdf:type trov:ArtifactArrangement .
            ?arrangement rdfs:comment ?name .
        }
        ORDER BY ?arrangement
        """
        self.tro["arrangements"] = {}
        self.dot.attr('node', shape='box', style='filled, rounded', fillcolor='#FFFFD1')
        res = self.graph.query(arrangement_qry)
        for row in res:
            if not str(row.arrangement) in self.tro["arrangements"]:
                self.tro["arrangements"][str(row.arrangement)] = {}
            self.tro["arrangements"][str(row.arrangement)]["name"] = str(row.name)
            self.dot.node(str(row.name))
        

    def get_artifacts(self):
        # Get all artifacts by arrangement
        artifact_location_qry = """
            SELECT DISTINCT ?arrangement ?sha256 ?location ?artifact ?excluded ?createdBy
            WHERE {
                ?locus trov:hasArtifact ?artifact .
                ?locus trov:hasLocation ?location .
                ?arrangement trov:hasLocus ?locus .
                ?arrangement rdf:type trov:ArtifactArrangement .
                ?artifact trov:sha256 ?sha256 .
                OPTIONAL {?locus trov:excluded ?excluded . }
                OPTIONAL {?locus trov:createdBy ?createdBy . }
            }
            ORDER by ?arrangement ?location
        """
        res = self.graph.query(artifact_location_qry)
        for row in res:
            if not "artifacts" in self.tro["arrangements"][str(row.arrangement)]:
                self.tro["arrangements"][str(row.arrangement)]["artifacts"] = {}   
            self.tro["arrangements"][str(row.arrangement)]["artifacts"][str(row.location)] = { 
                "sha256": str(row.sha256) ,
                "excluded": str(row.excluded),
                "createdBy": str(row.createdBy)
            }
        
        # Detect changes between arrangements
        # Which files were added? Which files changed? Which files were removed?
        # Which files were added by the system (.docker_stats, etc)? Which by the researcher?

        keys = list(self.tro["arrangements"].keys())
        for location in self.tro["arrangements"][keys[1]]["artifacts"]:
            if location in self.tro["arrangements"][keys[0]]["artifacts"]:
                if self.tro["arrangements"][keys[1]]["artifacts"][location]["sha256"] != self.tro["arrangements"][keys[0]]["artifacts"][location]["sha256"]:
                    self.tro["arrangements"][keys[1]]["artifacts"][location]["status"] = "Changed"
                else:
                    self.tro["arrangements"][keys[1]]["artifacts"][location]["status"] = "Unchanged"
            else:
                self.tro["arrangements"][keys[1]]["artifacts"][location]["status"] = "Added"

    def get_trs_info(self):
        # Get the TRS information
        trs_info_query = """
        SELECT DISTINCT ?trs ?comment ?publicKey ?owner ?description ?contact
        WHERE {
            ?trs        rdf:type           trov:TrustedResearchSystem .
            ?trs        rdfs:comment       ?comment .
            ?trs        trov:publicKey     ?publicKey .
            ?trs        trov:owner         ?owner .
            ?trs        trov:description   ?description .
            ?trs        trov:contact       ?contact .
            ?capability rdf:type  ?type .
        }
        ORDER BY ?trs ?capability
        """
        res = self.graph.query(trs_info_query)
        for row in res:
            self.tro["trs"] = {
                "id": str(row.trs),
                "name": str(row.comment),
                "publicKey": str(row.publicKey),
                "owner": str(row.owner),
                "contact": str(row.contact),
                "description": str(row.description)
            }

    def get_trs_capabilities(self):
        # Get TRS Capabilities
        capabilities_query = """
        SELECT DISTINCT ?name ?description
        WHERE {
            ?trs        rdf:type            trov:TrustedResearchSystem .
            ?trs        trov:hasCapability  ?capability .
            OPTIONAL { ?capability trov:name           ?name . }
            OPTIONAL { ?capability trov:description     ?description . }    
        }
        ORDER BY ?trs ?capability
        """
        self.tro["trs"]["capabilities"] = []
        res = self.graph.query(capabilities_query)
        for row in res:
            self.tro["trs"]["capabilities"].append({
                "name": str(row.name),
                "description": str(row.description)
            })

    def get_trp_info(self):
        trp_query = """
        SELECT DISTINCT ?trp ?accessed ?contributed ?started ?ended ?description
        WHERE {
            ?trp   rdf:type    trov:TrustedResearchPerformance .
            ?trp   rdfs:comment ?description .
            ?trp   trov:accessedArrangement ?arr1 .
            ?trp   trov:modifiedArrangement ?arr2 .
            ?arr1  rdfs:comment ?accessed .
            ?arr2  rdfs:comment ?contributed .
            ?trp   trov:startedAtTime ?started .
            ?trp   trov:endedAtTime   ?ended .
        } 
        ORDER BY ?trp ?started
        """
        self.tro["trps"] = []
        res = self.graph.query(trp_query)
        self.dot.attr('node', shape='box3d', style='filled, rounded', fillcolor='#D6FDD0')
        self.dot.attr('edge', color='black')
        for row in res:
            self.tro["trps"].append({
                    "id": str(row.trp),
                    "description": str(row.description),
                    "accessed": str(row.accessed),
                    "contributed": str(row.contributed),
                    "started": str(row.started),  
                    "ended": str(row.started)         
                })
            self.dot.node(str(row.description))
            self.dot.edge(str(row.accessed), str(row.description) )
            self.dot.edge(str(row.description), str(row.contributed) )

    def render(self, template, report):
        self.dot.render('workflow', cleanup=True, format='png')

        with open(template) as file_:
            template = Template(file_.read())

        with open(report, "w") as fh:
            fh.write(template.render(tro=self.tro))


report = TROReport()
report.parse("test.jsonld")
report.render("tro.md.jinja2", "report.md")