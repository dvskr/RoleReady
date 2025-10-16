chrome.action.onClicked.addListener(async (tab) => {
  if (!tab.id) return;
  
  try {
    const [{ result } = {}] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        // heuristic selectors (tweak per site)
        const sel = [
          'div.show-more-less-html__markup', // LinkedIn JD body
          'div#jobDescriptionText',          // Indeed
          'section.description',             // Glassdoor
          'div[data-testid="job-description"]', // ZipRecruiter
          'div.job-description',             // Generic
          'div.description',                 // Generic
          '[class*="description"]',          // Generic class-based
          '[class*="job-description"]'       // Generic job-description
        ];
        
        for (const s of sel) {
          const el = document.querySelector(s);
          if (el && el.innerText.trim().length > 100) {
            return el.innerText.trim();
          }
        }
        
        // Fallback: look for any div with substantial text content
        const divs = document.querySelectorAll('div');
        for (const div of divs) {
          const text = div.innerText.trim();
          if (text.length > 200 && 
              (text.includes('experience') || text.includes('skills') || text.includes('requirements'))) {
            return text;
          }
        }
        
        return '';
      }
    });
    
    const jd = result || '';
    const url = new URL('http://localhost:3000/dashboard/editor');
    url.searchParams.set('jd', encodeURIComponent(jd.slice(0, 50000)));
    chrome.tabs.create({ url: url.toString() });
  } catch (error) {
    console.error('Extension error:', error);
    // Fallback: open editor without JD
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard/editor' });
  }
});
