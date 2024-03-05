# TRACE Report 

Preliminary attempt to generate a [TRO report](https://transparency-certified.github.io/trace-model/demo/02-tro-examples/03-skope-lbda-processing/products/report.html) using `rdflib` and Jinja2 based on the [trace-model](https://github.com/transparency-certified/trace-model).

The basics:
* Read `input/test.jsondl` using `rdflib.Graph`
* Use SPARQL to query graph
* Convert to structure that can be passed to Jinja
* Generate Markdown


## Thoughts about JSON-LD/RDF

* We can treat the declaration as JSON and access as a Python dictionary or treat it as JSON-LD and access via RDF/SPARQL
* JSON-LD/RDF:
  * Imposes a less efficient structure for processing
  * Imposes use of a number of additional tools/languages (at minimum `rdflib` and SPARQL)
  * To be useful, requires mapping to external vocabularies (the most practical being Schema.org/RO-Crate, but reasoning is limited)
    - TransparentResearchObject = https://schema.org/CreativeWork
    - TrustedResearchSystem = https://schema.org/Organization?
    - TrustedResearchPerformance = https://schema.org/Event  
  * This would also allow us to easily incoporate things like name, description, URL, contact, etc.
  * Requires collaborators (who care) to understand RDF
  * Raises the question of why RDF?

## Thoughts about additional POC features.
- Users should be able to exclude files submitted to the server (e.g., .venv) 
  as well as specify which files should be excluded from the resulting zip (currently .dockerignore)
- It might be useful to indicate that a file was excluded and why. Something
  like .traceignore with both path and reason (license, private, etc).
- Users could provide useful metadata during submission. For example, a
  trace.json with TRO name, description, creator info, data citation, etc.
- We could provide a way to indicate whether a file was created by the system 
  like .docker_stats, .entrypoint, etc.
- We need to provide some sort of environment description for the POC server. 
  - Since it's building an image, we could maybe push it somewhere?
- hadPerformanceAttribute and hasAttribute need to be an arrays?
- In this example:
  - IncludesAllInputData is false. But how do we know?
- It's unlikely that very file will be well-described (unless we provide a simple optional structure to do so)
- If a TRO modifies an input file, are we retaining both?
- PREMIS OWL? https://www.loc.gov/standards/premis/ontology/pdf/premis3-owl-guidelines-20220426.pdf


for a in artifacts:
    if a["aid"] == "arcp:/arrangement/1":
        print(f"\t\"{a['location']}\": {{\n\t\t\"path\": \"{a['sha256']}\",\n\t\t\"mimeType\": \"{a['mimeType']}\"\n \t}}," )