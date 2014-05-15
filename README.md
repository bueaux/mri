mri
===

Module for visualising binary files.

![alt text](https://github.com/bueaux/mri/raw/master/notepad.png)

### PE plugin
This is currently the only plugin. 

It generates curves for entropy (measured over 512 byte blocks), number of zero bytes over the same block.
It also shows density of pointers (values which point into the image), and density of references (number of times an address has been addressed by a pointer).

It also collects boundary and points such as section boundaries, and address of entrypoint.

### Example usage

```python
from mri.plugins import pe
from mri.graph import draw_graph_mpl # matplotlib output.

graph_data = pe.generate_graph_data("c:/windows/system32/notepad.exe")
draw_graph_mpl(graph_data, filename="notepad.png", title="notepad.exe", 
    legend=True, xlabel="File offset")
```

### TODO
Other filetypes with automated plugin selection.

Smart boundary/point labels.

D3js output method.