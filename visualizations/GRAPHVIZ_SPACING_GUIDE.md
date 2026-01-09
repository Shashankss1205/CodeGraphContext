# 📐 Graphviz Spacing Improvements

## ✅ What Changed

I've enhanced the Graphviz DOT export with **better spacing parameters** to increase vertical distance and improve readability.

### **New Spacing Parameters:**

```dot
digraph CodeGraph {
    // Layout settings for better spacing
    rankdir=TB;                    // Top to Bottom layout
    ranksep=1.5;                   // ⬆️ Vertical spacing between ranks (was default 0.5)
    nodesep=0.8;                   // ⬅️➡️ Horizontal spacing between nodes (was default 0.25)
    splines=ortho;                 // Orthogonal edges for cleaner look
    
    // Enhanced node styling
    node [
        shape=box,
        style="filled,rounded",    // Rounded corners
        fillcolor=lightblue,
        fontname="Arial",
        fontsize=12,
        margin=0.3,                // Internal padding
        height=0.6                 // Minimum node height
    ];
    
    // Enhanced edge styling
    edge [
        color=gray,
        arrowsize=0.8,
        penwidth=1.5               // Thicker edges
    ];
}
```

## 📊 **Key Improvements:**

### **1. Increased Vertical Distance**
- **`ranksep=1.5`** - Increases vertical spacing between levels by **3x** (default is 0.5)
- This gives you much more breathing room between function calls

### **2. Better Horizontal Spacing**
- **`nodesep=0.8`** - Increases horizontal spacing by **3.2x** (default is 0.25)
- Prevents nodes from overlapping or being too close

### **3. Cleaner Edge Routing**
- **`splines=ortho`** - Uses orthogonal (right-angle) edges instead of curved
- Creates a more structured, grid-like appearance
- **Note**: Edge labels may not show with ortho splines (see alternatives below)

### **4. Better Node Appearance**
- Rounded corners for modern look
- Consistent font (Arial)
- Larger font size (12pt)
- More internal padding

---

## 🎨 **Generated Files:**

✅ **calls.png** - Function call graph with improved spacing  
✅ **imports.png** - Import dependency graph with improved spacing  
✅ **inherits.png** - Class inheritance tree with improved spacing  

---

## 🔧 **Alternative Spacing Options:**

If you want **even more** vertical spacing, you can manually edit the DOT files:

### **For Maximum Vertical Spacing:**
```dot
ranksep=2.5;        // Even more vertical space
nodesep=1.2;        // Even more horizontal space
```

### **For Edge Labels (if needed):**
If you need edge labels to show, change:
```dot
splines=polyline;   // Instead of ortho
```
Or use:
```dot
splines=curved;     // Smooth curved edges (default)
```

---

## 📏 **Spacing Parameter Guide:**

| Parameter | Default | New Value | Effect |
|-----------|---------|-----------|--------|
| `ranksep` | 0.5 | **1.5** | 3x more vertical space |
| `nodesep` | 0.25 | **0.8** | 3.2x more horizontal space |
| `splines` | curved | **ortho** | Cleaner, grid-like edges |
| `height` | 0.5 | **0.6** | Taller nodes |
| `margin` | 0.11 | **0.3** | More padding inside nodes |

---

## 🎯 **How to Customize Further:**

### **1. Edit the DOT files directly:**
```bash
nano option_b_graphviz_calls.dot
# Change ranksep=1.5 to ranksep=3.0 for even more space
```

### **2. Regenerate with custom spacing:**
```bash
dot -Tpng -Granksep=3.0 -Gnodesep=1.5 option_b_graphviz_calls.dot -o calls_extra_spaced.png
```

### **3. Try different layouts:**
```bash
# Left to Right instead of Top to Bottom
dot -Tpng -Grankdir=LR option_b_graphviz_calls.dot -o calls_lr.png

# Use different layout engine
neato -Tpng option_b_graphviz_calls.dot -o calls_neato.png  # Force-directed
fdp -Tpng option_b_graphviz_calls.dot -o calls_fdp.png      # Force-directed with clustering
circo -Tpng option_b_graphviz_calls.dot -o calls_circo.png  # Circular layout
```

---

## 💡 **Recommended Settings by Use Case:**

### **For Presentations (Maximum Clarity):**
```dot
ranksep=2.5;
nodesep=1.5;
splines=polyline;
fontsize=14;
```

### **For Documentation (Balanced):**
```dot
ranksep=1.5;        // Current setting
nodesep=0.8;        // Current setting
splines=ortho;      // Current setting
```

### **For Compact View (Space-Saving):**
```dot
ranksep=0.8;
nodesep=0.5;
splines=curved;
```

---

## 🖼️ **View Your Images:**

```bash
# Open all generated PNGs
xdg-open calls.png
xdg-open imports.png
xdg-open inherits.png
```

---

**The new spacing settings should give you much better vertical distance in your diagrams!** 🎉
