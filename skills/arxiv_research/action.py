import arxiv
import os

def execute(task=None):
    """
    Searches Arxiv for papers.
    Task: '[query]'
    """
    if not task:
        return "Arxiv Error: No search query provided."
    
    print(f"Searching Arxiv for: {task}...")
    
    try:
        client = arxiv.Client()
        search = arxiv.Search(
            query=task,
            max_results=3,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        for result in client.results(search):
            results.append(f"Title: {result.title}\nAuthors: {[a.name for a in result.authors]}\nSummary: {result.summary[:300]}...\nLink: {result.pdf_url}\n")
        
        if not results:
            return f"No Arxiv papers found for '{task}'."
            
        return "--- Arxiv Academic Pulse ---\n\n" + "\n".join(results)
    except Exception as e:
        return f"Arxiv Search Error: {str(e)}"
