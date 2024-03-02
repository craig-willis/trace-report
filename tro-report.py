import graphviz
from jinja2 import Template
import urllib.parse
from rdflib import Graph
from collections import defaultdict

# Needed to parse the @base
urllib.parse.uses_relative.append("arcp")


class TROReport:
    graph = None
    tro = {}

    def parse(self, location):
        self.graph = Graph()
        self.graph.parse(location=location, format="json-ld")

        self.get_tro_info()
        self.get_trs_info()
        self.get_trp_info()
        self.get_arrangements()
        self.get_artifacts()
        self.get_trs_capabilities()

    # Convert SPARQL result row to dict
    def result_to_dict(self, res):
        return [
            dict(line)
            for line in [
                zip([str(x) for x in res.vars], [str(x) for x in row]) for row in res
            ]
        ]

    def get_tro_info(self):
        # Name, description, createdBy, and createdDate were added to POC report
        tro_info_qry = """
        SELECT DISTINCT ?tro ?name ?description ?createdBy ?createdDate
        WHERE {
            ?tro    rdf:type          trov:TransparentResearchObject .
            ?tro    trov:name         ?name .
            ?tro    trov:description  ?description .
            ?tro    trov:createdBy    ?createdBy .
            ?tro    trov:createdDate  ?createdDate .
        }
        """
        res = self.graph.query(tro_info_qry)
        self.tro = self.result_to_dict(res)[0]

    def get_arrangements(self):
        # Get the list of arrangements
        # TODO: Comment should just be name
        arrangement_qry = """
        SELECT DISTINCT (STR(?arrangement) AS ?id) ?name
        WHERE {
            ?arrangement rdf:type trov:ArtifactArrangement .
            ?arrangement rdfs:comment ?name .
        }
        ORDER BY ?id
        """
        res = self.graph.query(arrangement_qry)
        arr = self.result_to_dict(res)

        self.tro["arrangements"] = defaultdict(dict)
        for a in arr:
            self.tro["arrangements"][a["id"]]["name"] = a["name"]

    def get_artifacts(self):
        # Get all artifacts by arrangement
        artifact_location_qry = """
            SELECT DISTINCT (STR(?arrangement) AS ?aid) ?sha256 ?location ?artifact ?excluded ?createdBy
            WHERE {
                ?locus trov:hasArtifact ?artifact .
                ?locus trov:hasLocation ?location .
                ?arrangement trov:hasLocus ?locus .
                ?arrangement rdf:type trov:ArtifactArrangement .
                ?artifact trov:sha256 ?sha256 .
                OPTIONAL {?locus trov:excluded ?excluded . }
                OPTIONAL {?locus trov:createdBy ?createdBy . }
            }
            ORDER by ?aid ?location
        """
        res = self.graph.query(artifact_location_qry)
        artifacts = self.result_to_dict(res)
        for artifact in artifacts:
            if "artifacts" not in self.tro["arrangements"][artifact["aid"]]:
                self.tro["arrangements"][artifact["aid"]]["artifacts"] = {}
            self.tro["arrangements"][artifact["aid"]]["artifacts"][
                artifact["location"]
            ] = {k: artifact[k] for k in ("sha256", "excluded", "createdBy")}

        # Detect changes between arrangements
        # Which files were added? Which files changed? Which files
        # were removed?  Which files were added by the system
        # (.docker_stats, etc)? Which by the researcher?
        keys = list(self.tro["arrangements"].keys())
        for location in self.tro["arrangements"][keys[1]]["artifacts"]:
            if location in self.tro["arrangements"][keys[0]]["artifacts"]:
                if (
                    self.tro["arrangements"][keys[1]]["artifacts"][location]["sha256"]
                    != self.tro["arrangements"][keys[0]]["artifacts"][location]["sha256"]
                ):
                    self.tro["arrangements"][keys[1]]["artifacts"][location]["status"] = "Changed"
                else:
                    self.tro["arrangements"][keys[1]]["artifacts"][location]["status"] = "Unchanged"
            else:
                self.tro["arrangements"][keys[1]]["artifacts"][location]["status"] = "Added"

    def get_trs_info(self):
        # Get the TRS information
        trs_info_query = """
        SELECT DISTINCT (STR(?trp) AS ?id)  ?comment ?publicKey ?owner ?description ?contact ?url
        WHERE {
            ?trs        rdf:type           trov:TrustedResearchSystem .
            ?trs        rdfs:comment       ?comment .
            ?trs        trov:publicKey     ?publicKey .
            ?trs        trov:owner         ?owner .
            ?trs        trov:description   ?description .
            ?trs        trov:contact       ?contact .
            ?trs        trov:url           ?url .
            ?capability rdf:type  ?type .
        }
        ORDER BY ?trs ?capability
        """
        res = self.graph.query(trs_info_query)
        trs = self.result_to_dict(res)
        self.tro["trs"] = trs[0]

    def get_trs_capabilities(self):
        # Get TRS Capabilities
        capabilities_query = """
        SELECT DISTINCT ?name ?description
        WHERE {
            ?trs        rdf:type                    trov:TrustedResearchSystem .
            ?trs        trov:hasCapability          ?capability .
            OPTIONAL { ?capability trov:name        ?name . }
            OPTIONAL { ?capability trov:description ?description . }
        }
        ORDER BY ?trs ?capability
        """
        res = self.graph.query(capabilities_query)
        self.tro["trs"]["capabilities"] = self.result_to_dict(res)

    def get_trp_info(self):
        trp_query = """
        SELECT DISTINCT (STR(?trp) AS ?id) ?accessed ?contributed ?started ?ended ?description
        WHERE {
            ?trp   rdf:type                 trov:TrustedResearchPerformance .
            ?trp   rdfs:comment             ?description .
            ?trp   trov:accessedArrangement ?arr1 .
            ?trp   trov:modifiedArrangement ?arr2 .
            ?arr1  rdfs:comment             ?accessed .
            ?arr2  rdfs:comment             ?contributed .
            ?trp   trov:startedAtTime       ?started .
            ?trp   trov:endedAtTime         ?ended .
        }
        ORDER BY ?trp ?started
        """
        res = self.graph.query(trp_query)
        self.tro["trps"] = self.result_to_dict(res)

    # Do the Graphviz
    def generate_digraph(self):
        dot = graphviz.Digraph("TRO")
        dot.graph_attr["rankdir"] = "LR"
        dot.attr("edge", color="black")
        dot.graph_attr["dpi"] = "200"

        dot.attr("node", shape="box", style="filled, rounded", fillcolor="#FFFFD1")
        for arrangement in self.tro["arrangements"]:
            dot.node(self.tro["arrangements"][arrangement]["name"])

        dot.attr("node", shape="box3d", style="filled, rounded", fillcolor="#D6FDD0")
        for trp in self.tro["trps"]:
            dot.node(trp["description"])
            dot.edge(trp["accessed"], trp["description"])
            dot.edge(trp["description"], trp["contributed"])

        dot.render("workflow", "output", cleanup=True, format="png")

    def render(self, template, report):

        self.generate_digraph()
        with open(template) as file_:
            template = Template(file_.read())

        with open(report, "w") as fh:
            fh.write(template.render(tro=self.tro))


report = TROReport()
report.parse("input/test.jsonld")
report.render("templates/tro.md.jinja2", "output/report.md")
