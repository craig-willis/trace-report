# TRACE Report 

Super hacky TRO report using SPARKLE! (Based on the `trace-model` report generator).

## Thoughts
- Users should be able to exclude files submitted to the server (e.g., .venv) 
  as well as specify which files should be excluded from the resulting zip (currently .dockerignore)
- It might be useful to indicate that a file was excluded and why. Something
  like .traceignore with both path and reason (license, private, etc).
- Users could provide useful metadata during submission. For example, a
  trace.json with TRO name, description, creator info, data citation, etc.
- We could provide a way to indicate whether a file was created by the system 
  like .docker_stats, .entrypoint, etc.
- If we're using JSON-LD, we should really tie things to other schemas/vocabularies. This 
  would allow us to specify obvious things like names, decscriptions, URLs, contact info, etc. 
  in a standard way. But this depends on how intent we are to have deeper OWL-based reasoning
  - TransparentResearchObject = https://schema.org/CreativeWork
  - TrustedResearchSystem = https://schema.org/Organization?
  - TrustedResearchPerformance = https://schema.org/Event
- We need to provide some sort of environment description for the POC server. 
  - Since it's building an image, we could maybe push it somewhere?
- hadPerformanceAttribute and hasAttribute need to be an arrays?
- In this example:
  - IncludesAllInputData is false. But how do we know?
- TRS capabilities need to be defined in a standard vocabulary
- It's unlikely that very file will be well-described (unless we provide a simple optional structure to do so)

