// Debug script for Discovery Wizard
// Run this in the browser console to test the discovery wizard

console.log('=== Discovery Wizard Debug ===');

// Test 1: Check if the wizard class exists
console.log('1. Checking if CameraDiscoveryWizard class exists...');
if (typeof CameraDiscoveryWizard !== 'undefined') {
    console.log('✓ CameraDiscoveryWizard class found');
} else {
    console.log('✗ CameraDiscoveryWizard class NOT found');
}

// Test 2: Check if the wizard instance exists
console.log('2. Checking if discoveryWizard instance exists...');
if (typeof window.discoveryWizard !== 'undefined') {
    console.log('✓ discoveryWizard instance found');
} else {
    console.log('✗ discoveryWizard instance NOT found');
}

// Test 3: Check if the discovery wizard button exists
console.log('3. Checking if discovery wizard button exists...');
const discoveryBtn = document.getElementById('discovery-wizard-btn');
if (discoveryBtn) {
    console.log('✓ Discovery wizard button found');
    console.log('Button HTML:', discoveryBtn.outerHTML);
    console.log('Button visible:', discoveryBtn.offsetParent !== null);
} else {
    console.log('✗ Discovery wizard button NOT found');
}

// Test 4: Check if the discovery wizard modal exists
console.log('4. Checking if discovery wizard modal exists...');
const modal = document.getElementById('discovery-wizard-modal');
if (modal) {
    console.log('✓ Discovery wizard modal found');
    console.log('Modal display style:', window.getComputedStyle(modal).display);
} else {
    console.log('✗ Discovery wizard modal NOT found');
}

// Test 5: Check if cameras section is visible
console.log('5. Checking cameras section visibility...');
const camerasSection = document.getElementById('cameras');
if (camerasSection) {
    console.log('✓ Cameras section found');
    console.log('Cameras section visible:', camerasSection.offsetParent !== null);
    console.log('Cameras section display:', window.getComputedStyle(camerasSection).display);
} else {
    console.log('✗ Cameras section NOT found');
}

// Test 6: Try to manually trigger the wizard
console.log('6. Attempting to manually trigger wizard...');
if (window.discoveryWizard) {
    try {
        window.discoveryWizard.manualTrigger();
        console.log('✓ Manual trigger successful');
    } catch (error) {
        console.log('✗ Manual trigger failed:', error.message);
    }
} else {
    console.log('✗ Cannot test manual trigger - discoveryWizard not available');
}

// Test 7: Try to click the button programmatically
console.log('7. Attempting to click discovery wizard button...');
if (discoveryBtn) {
    try {
        discoveryBtn.click();
        console.log('✓ Button click successful');
    } catch (error) {
        console.log('✗ Button click failed:', error.message);
    }
} else {
    console.log('✗ Cannot test button click - button not found');
}

// Test 8: Navigation to cameras page
console.log('8. Attempting to navigate to cameras page...');
if (window.app && typeof window.app.navigateToPage === 'function') {
    try {
        window.app.navigateToPage('cameras');
        console.log('✓ Navigation to cameras page successful');
        
        // Recheck button after navigation
        setTimeout(() => {
            const discoveryBtnAfterNav = document.getElementById('discovery-wizard-btn');
            if (discoveryBtnAfterNav) {
                console.log('✓ Discovery wizard button found after navigation');
                console.log('Button visible after navigation:', discoveryBtnAfterNav.offsetParent !== null);
            } else {
                console.log('✗ Discovery wizard button still not found after navigation');
            }
        }, 100);
    } catch (error) {
        console.log('✗ Navigation failed:', error.message);
    }
} else {
    console.log('✗ Cannot test navigation - app.navigateToPage not available');
}

console.log('=== Debug Complete ===');