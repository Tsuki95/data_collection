# Method overview  
**1. Auto method 1（批量PDF分析，表格形式，xyz结构文件）:**   
	先从CSD里搜索到双核金结构的DOI，然后使用web of science+zotero下载文献PDF到本地，继而用大模型分析氧化还原电势信息和对应结构到excel，再从CSD里下载结构的xyz文件。  

**2. Auto method 2（批量PDF分析，表格形式，xyz结构文件）:**  
	先从CSD里搜索到双核金结构的DOI，然后在校园网下爬取文献PDF到本地，继而用大模型分析氧化还原电势信息和对应结构到excel，再从CSD里下载结构的xyz文件。  
	**问题**  
 爬虫未能解决人机验证问题  

**3. Auto method 3（多个PDF分析，word形式，结构图片）:**  
	对已经下载到本地的PDF文件，先用大模型进行氧化还原电势信息分析并提取结构图片信息，再用pdf extract kit进行布局分析，然后将对应图片拉取出来，和之前的电势信息汇总到一个word。  

**4. Auto method 4（多个PDF分析，word形式，结构图片）:**  
	对已经下载到本地的PDF文件，先用大模型进行氧化还原电势信息分析并提取结构图片信息，再用MinerU里的Magic pdf将pdf转换成markdown格式，然后将对应图片拉取出来，和之前的电势信息汇总到一个word。  
	**问题**  
 因为多了一步转换为markdown所以较慢(作为参考，分析单个pdf使用method 3即可)

****
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

****
# Auto method 2:
**Preparation：**

1. 安装`CSD python api`环境
2. 依赖包(版本兼容即可)：  
	`pandas  
	openai  
	playwright   
	langchain-community   
	langchain-core`  

**注：**  
此方法会打开一个虚拟的Google浏览器，在里面进行检索，需要按照这个网站的方法修改Google浏览器属性  
https://www.bilibili.com/video/BV1xP411Q7LM/?vd_source=c60eedf38c16689fccaa69edc9f75b21  

**Instruction:**

1. 在`windows校园网`下直接运行`run_all_scripts.py`就会生成所有文件。
2. 如果不搜索双核金，需要在`CSD_search.py`中更改和`Auto method 1`类似的位置。

**Problems:**

1. 有时候网站出现`“verify you are human”`之类的人机验证，就爬取不到文献内容了；但不会报错，会继续爬下一个url。
2. 用免费的`deepseek`读取网站内容非常慢(读取pdf内容很快)，但是`gpt-4o-mini`读取都较快，故此处用不免费但较便宜的`gpt-4o-mini`。

****
# Auto method 3:
**Preparation：**

1. 建一个`python 3.10`的环境
2. 依赖包(版本兼容即可)：  
	`PyPDF2   
	docx   
	openai   
	tiktoken`

**Instruction:**

1. 删去`pdf`下的其他文件，将要分析的文献放入此中。
2. 直接运行`run.py`，然后就会在`word`文件夹里生成带有结构图片的分析结果文件。

**注：**
如果需要更改存放文件的位置，请更改`run.py`和`PDF-Extract-Kit-main\configs\layout_detection_yolo.yaml`配置文件:  
`run.py`  
```
BASE_DIR = os.path.abspath(".")
WORD_FILE_PATH = r'E:\\data_collection-main\\Auto_method_3\\word'  # 保存提取后的文本的文件路径
PDF_DIR_PATH = r'E:\\data_collection-main\\Auto_method_3\\pdf'  # PDF 文件所在的文件夹路径
OUTPUT_DIR_PATH = r'E:\\data_collection-main\\Auto_method_3\\outputs'  # 输出文件夹路径
```
`PDF-Extract-Kit-main\configs\layout_detection_yolo.yaml`  
```
outputs: outputs
```

****
# Auto method 4:
**Preparation：**

1. 建一个`python 3.10`的环境  
2. 下载`MinerU`包  
3. 依赖包(版本兼容即可)：  
	`docx   
	markdown   
	beautifulsoup  
	pylatexenc  
	PyPDF2   
	openai   
	tiktoken`

**Instruction:**

1. 在`run_all_scripts.py`更改需要分析的pdf路径，然后直接运行`run_all_scripts.py`, 就会生成所有输出文件。
```
# Configure paths
current_dir = os.path.dirname(os.path.abspath(__file__)) # 获取当前脚本所在的目录
pdf_dir = os.path.join(current_dir, "pdf") # pdf文件夹路径

output = os.path.join(current_dir, "outputs", pdf_filename_no_ext) # 输出文件夹路径
```

**注：**
1. 从`https://github.com/opendatalab/MinerU`里按要求下载`MinerU`包和`Magic PDF`  
```
pip install -U "magic-pdf[full]" --extra-index-url https://wheels.myhloli.com
```
2. 在`pdf2markdown.py`里将`magic_pdf`的路径更改为下载后的保存路径
```
mineru_path = r'E:\\crawler\\MinerU\\MinerU-master\\magic_pdf'  # 替换为你的 MinerU 路径
sys.path.append(mineru_path)
```
3. 在`run_all_scripts.py`中按需更改要分析的PDF文件路径和输出文件目录  
```
# Configure paths
current_dir = os.path.dirname(os.path.abspath(__file__)) # 获取当前脚本所在的目录
pdf_dir = os.path.join(current_dir, "pdf") # pdf文件夹路径

output = os.path.join(current_dir, "outputs", pdf_filename_no_ext) # 输出文件夹路径
```



































