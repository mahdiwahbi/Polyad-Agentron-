# Polyad API Documentation

## Class: Polyad

### Constructor
```python
polyad = Polyad()
```
Initializes the agent with optimal resource configuration.

### Methods
#### run(task: str) -> str
```python
response = polyad.run("Analyze the market trends")
```
Executes a task with automatic parallel/sequential processing selection.

#### parallel_inference(task: str) -> str
Internal method for parallel processing using Mercury-style diffusion.

## Class: ResourceManager

### Methods
#### get_optimal_model() -> str
Selects between models based on available RAM:
- gemma3:12b-q4_0 (>10GB RAM)
- gemma3:12b-q2_K (>6GB RAM)

#### monitor_resources() -> dict
Returns current system status including:
- CPU usage
- Available RAM
- GPU availability
- Temperature

## Class: PolyadTools

### Methods
#### web_search(query: str) -> str
Performs web search using DuckDuckGo.

#### process_image(image_path: str) -> ndarray
Processes and caches image operations.
