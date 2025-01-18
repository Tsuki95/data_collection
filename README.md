# Method overview  
**1. Auto method 1（批量PDF分析，表格形式，xyz结构文件）:**   
	先从CSD里搜索到双核金结构的DOI，然后使用web of science+zotero下载文献PDF到本地，继而用大模型分析氧化还原电势信息和对应结构到excel，再从CSD里下载结构的xyz文件。  

**2. Auto method 2（批量PDF分析，表格形式，xyz结构文件）:**  
	先从CSD里搜索到双核金结构的DOI，然后在校园网下爬取文献PDF到本地，继而用大模型分析氧化还原电势信息和对应结构到excel，再从CSD里下载结构的xyz文件。  
	**问题**  
 爬虫未能解决人机验证问题  

**3. Auto method 3（单个PDF分析，word形式，结构图片）:**  
	对已经下载到本地的单个PDF文件，先用大模型进行氧化还原电势信息分析并提取结构图片信息，再用pdf extract kit进行布局分析，然后将对应图片拉取出来，和之前的电势信息汇总到一个word。  

**4. Auto method 4（单个PDF分析，word形式，结构图片）:**  
	对已经下载到本地的单个PDF文件，先用大模型进行氧化还原电势信息分析并提取结构图片信息，再用MinerU里的Magic pdf将pdf转换成markdown格式，然后将对应图片拉取出来，和之前的电势信息汇总到一个word。  
	**问题**  
 因为多了一步转换为markdown所以较慢(作为参考，分析单个pdf使用method 3即可)

# Auto method 1:
**Preparation：**

1. 安装`CSD python api`环境
2. 依赖包(版本兼容即可)：  
	`pandas  
	PyPDF2  
	openai  
	tiktoken  
	re`

**Instruction:**

1. 运行`CSD_search.py`, 如果不搜索双核金，需要更改这些位置：
```
  # Define the target substructure [Au]-[Au]
  specified = ccdc.search.SMARTSSubstructure("[Au]-[Au]")                 #--> [Au]-[Au]
```
```  
  settings.must_not_have_elements = ['Re', 'Ir', 'As', 'Cu', 'Os', 'Fe', 'Co', 'Ru', 'W', 'B', 'Ag', 'Li', 'Se', 'Si', 'Rh', 'Mn', 'Pd', 'Ge', 'Sb', 'Sn']   # --> Remove unwanted elements
  substructure_search.add_substructure(specified)
```
```
  # Filter molecules that contain Au2 in the formula
  for i in range(len(hits)):
      id = hits[i].identifier
      hit = csd_reader.entry(id)
      formula = hit.molecule.formula
      if 'Au2 ' in formula:                                               # --> check if 'Au2' in formula
          specified_molecules.append(hits[i].identifier)
```             
2. 然后可以得到一个`molecule_doi_info.csv`, 将其中的`url`这一列的链接全部复制粘贴到`web of science`里进行搜索。
     https://www.webofscience.com/wos/alldb/basic-search
3. 全选搜索到的所有文献，然后`export RIS`格式到本地。  
4. 在`Zotero`里选择“文件”-->”导入”，将RIS导入到Zotero的任意目录。  
5. 在`Zotero`里全选导入的文献，右键点击“查找全文”然后Zotero会自动检索PDF。  
6. 在`Zotero`里全选检索完PDF的所有文献，再选择“文件”-->”导出PDF”，将所有文献的PDF导入本地文件夹。  
7. 然后运行`pdf_analysis.py`，得到刚下载的文献的分析结果，提取了所有氧化还原电势。  
8. 然后运行`xyz_download.py`，得到分析结果中CSD编号对应的CSD晶体学数据库中的结构的xyz文件。  

# Auto method 2:
**Preparation：**

1. 安装CSD python api环境
2. 依赖包(版本兼容即可)：  
	`pandas  
	openai  
	playwright   
	langchain-community   
	langchain-core`  





















