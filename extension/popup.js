// Popup script for RoleReady Professional Extension

document.addEventListener('DOMContentLoaded', function() {
  const statusEl = document.getElementById('status');
  
  // Update status message
  function updateStatus(message) {
    statusEl.textContent = message;
    setTimeout(() => {
      statusEl.textContent = 'Ready';
    }, 3000);
  }
  
  // Get current tab
  async function getCurrentTab() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab;
  }
  
  // Scrape JD and open editor
  document.getElementById('scrapeJD').addEventListener('click', async () => {
    try {
      const tab = await getCurrentTab();
      updateStatus('Scraping JD...');
      
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'SCRAPE_JD' });
      
      if (response && response.jd) {
        const editorUrl = `http://localhost:3000/dashboard/editor?jd=${encodeURIComponent(response.jd)}`;
        chrome.tabs.create({ url: editorUrl });
        updateStatus('JD sent to editor!');
      } else {
        updateStatus('No JD found on this page');
      }
    } catch (error) {
      console.error('Error scraping JD:', error);
      updateStatus('Error: Check if on job site');
    }
  });
  
  // Copy JD to clipboard
  document.getElementById('copyJD').addEventListener('click', async () => {
    try {
      const tab = await getCurrentTab();
      updateStatus('Copying JD...');
      
      const response = await chrome.tabs.sendMessage(tab.id, { type: 'SCRAPE_JD' });
      
      if (response && response.jd) {
        await navigator.clipboard.writeText(response.jd);
        updateStatus('JD copied to clipboard!');
      } else {
        updateStatus('No JD found on this page');
      }
    } catch (error) {
      console.error('Error copying JD:', error);
      updateStatus('Error: Unable to copy');
    }
  });
  
  // Autofill form
  document.getElementById('autofill').addEventListener('click', async () => {
    try {
      const tab = await getCurrentTab();
      
      // Get stored profile
      const result = await chrome.storage.sync.get(['userProfile']);
      const profile = result.userProfile;
      
      if (!profile) {
        updateStatus('No profile found. Set up profile first.');
        return;
      }
      
      updateStatus('Autofilling form...');
      
      // Send autofill message to content script
      await chrome.tabs.sendMessage(tab.id, { 
        type: 'AUTOFILL', 
        profile: profile 
      });
      
      updateStatus('Form autofilled!');
    } catch (error) {
      console.error('Error autofilling:', error);
      updateStatus('Error: Unable to autofill');
    }
  });
  
  // Manage profile
  document.getElementById('manageProfile').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  });
  
  // Open dashboard
  document.getElementById('openDashboard').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard' });
  });
  
  // Open editor
  document.getElementById('openEditor').addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000/dashboard/editor' });
  });
  
  // Check if we're on a supported job site
  getCurrentTab().then(tab => {
    const url = tab.url.toLowerCase();
    const supportedSites = ['linkedin.com', 'indeed.com', 'glassdoor.com', 'ziprecruiter.com', 'monster.com', 'careerbuilder.com'];
    
    const isSupported = supportedSites.some(site => url.includes(site));
    
    if (!isSupported) {
      updateStatus('⚠️ Not on a supported job site');
    }
  });
});
