function scrapeJD() {
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

// Safe autofill functionality
const fieldMappings = {
  name: [/name/i, /full.?name/i, /first.?name/i, /last.?name/i, /given.?name/i, /family.?name/i],
  email: [/email/i, /e.?mail/i, /mail/i],
  phone: [/phone/i, /mobile/i, /cell/i, /telephone/i, /contact.?number/i],
  location: [/address/i, /location/i, /city/i, /state/i, /country/i, /zip/i, /postal/i],
  linkedin: [/linkedin/i, /linked.?in/i],
  github: [/github/i, /git.?hub/i],
  summary: [/summary/i, /objective/i, /profile/i, /about/i, /bio/i]
};

function assignValue(input, value) {
  if (!value) return false;
  
  // Set the value
  input.value = value;
  
  // Trigger events to ensure form validation works
  input.dispatchEvent(new Event('input', { bubbles: true }));
  input.dispatchEvent(new Event('change', { bubbles: true }));
  input.dispatchEvent(new Event('blur', { bubbles: true }));
  
  return true;
}

function safeAutofill(profile) {
  if (!profile) return;
  
  const inputs = Array.from(document.querySelectorAll('input, textarea, select'));
  let filledCount = 0;
  
  for (const input of inputs) {
    // Skip hidden, disabled, or readonly inputs
    if (input.type === 'hidden' || input.disabled || input.readOnly) {
      continue;
    }
    
    // Get field identifier
    const name = (input.name || '').toLowerCase();
    const id = (input.id || '').toLowerCase();
    const placeholder = (input.placeholder || '').toLowerCase();
    const label = (input.closest('label')?.textContent || '').toLowerCase();
    
    const fieldText = `${name} ${id} ${placeholder} ${label}`.toLowerCase();
    
    // Check each field type
    for (const [fieldType, patterns] of Object.entries(fieldMappings)) {
      if (patterns.some(pattern => pattern.test(fieldText))) {
        let value = null;
        
        // Get appropriate value based on field type
        switch (fieldType) {
          case 'name':
            value = profile.name;
            break;
          case 'email':
            value = profile.email;
            break;
          case 'phone':
            value = profile.phone;
            break;
          case 'location':
            value = profile.location;
            break;
          case 'linkedin':
            value = profile.linkedin_url || profile.links?.linkedin;
            break;
          case 'github':
            value = profile.github_url || profile.links?.github;
            break;
          case 'summary':
            value = profile.summary;
            break;
        }
        
        if (assignValue(input, value)) {
          filledCount++;
          console.log(`Autofilled ${fieldType}:`, value);
        }
        break; // Only fill one field type per input
      }
    }
  }
  
  console.log(`RoleReady: Autofilled ${filledCount} fields`);
  return filledCount;
}

// Message listener
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === 'SCRAPE_JD') {
    sendResponse({ jd: scrapeJD() });
  } else if (msg.type === 'AUTOFILL' && msg.profile) {
    const filledCount = safeAutofill(msg.profile);
    sendResponse({ filledCount });
  }
});
