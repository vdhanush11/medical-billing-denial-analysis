# 📊 Medical Billing Denial Analysis

An interactive **Streamlit** dashboard for analyzing healthcare claim denials. Upload your CSV or Excel claims data to explore top denied CPT codes, denial rates by payer and provider, root causes of denials, and recommended fixes. The app also provides visual reports, including bar charts and heatmaps.

---

## **Features**

- Normalize and detect common column names automatically
- Calculate denial rates and lost revenue per CPT, payer, and provider
- Identify root causes of denials:
  - Modifier issues
  - LCD/NCD mismatches
  - Bundling edits (NCCI)
  - Lack of documentation
  - Prior authorization problems
  - Credentialing issues
- Provide recommended strategies and workflow improvements
- Interactive visualizations:  
  - CPT denial rate and count  
  - Denials by payer  
  - Denials by provider  
  - Heatmaps for CPT vs Payer/Provider denial rates  

---

## **Tech Stack**

- Python  
- Streamlit  
- Pandas, NumPy  
- Matplotlib, Seaborn  

