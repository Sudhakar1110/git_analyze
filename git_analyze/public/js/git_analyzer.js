// Git Analyzer Portal JS
frappe.provide('git_analyzer');

git_analyzer.init = function() {
    git_analyzer.bindEvents();
};

git_analyzer.bindEvents = function() {
    // Analysis form submit
    const form = document.getElementById('analysis-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            git_analyzer.submitAnalysis();
        });
    }

    // Settings form submit
    const settingsForm = document.getElementById('settings-form');
    if (settingsForm) {
        settingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            git_analyzer.saveSettings();
        });
    }

    // Filter tabs
    document.querySelectorAll('.ga-filter-tab').forEach(function(tab) {
        tab.addEventListener('click', function() {
            document.querySelectorAll('.ga-filter-tab').forEach(function(t) {
                t.classList.remove('active');
            });
            this.classList.add('active');
            git_analyzer.filterResults(this.dataset.filter);
        });
    });

    // Search
    const searchInput = document.getElementById('search-results');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            git_analyzer.searchResults(this.value);
        });
    }
};

git_analyzer.submitAnalysis = function() {
    const url = document.getElementById('github-url').value;
    const branch = document.getElementById('branch').value || 'main';
    const depth = document.getElementById('depth').value;
    const questions = document.getElementById('questions').value;

    if (!url) {
        frappe.msgprint('Please enter a GitHub URL');
        return;
    }

    const btn = document.getElementById('submit-btn');
    btn.disabled = true;
    btn.innerHTML = '<span class="ga-progress-spinner" style="width:16px;height:16px;border-width:2px;"></span> Analyzing...';

    document.getElementById('analysis-form').style.display = 'none';
    document.getElementById('analysis-progress').style.display = 'block';

    frappe.call({
        method: 'git_analyze.api.analyze_repo',
        args: {
            github_url: url,
            branch: branch,
            depth: depth,
            questions: questions
        },
        callback: function(r) {
            if (r.message && r.message.name) {
                frappe.msgprint({
                    title: 'Analysis Started',
                    indicator: 'green',
                    message: 'Analysis ' + r.message.name + ' has been queued. You will be redirected to the results page.'
                });
                setTimeout(function() {
                    window.location.href = '/git-analyzer/results';
                }, 2000);
            }
        },
        error: function(r) {
            frappe.msgprint({
                title: 'Error',
                indicator: 'red',
                message: r.message || 'Failed to start analysis'
            });
            document.getElementById('analysis-form').style.display = 'block';
            document.getElementById('analysis-progress').style.display = 'none';
            btn.disabled = false;
            btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M2 8L8 2L14 8M8 2V14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg> Start Analysis';
        }
    });
};

git_analyzer.saveSettings = function() {
    const groqKey = document.getElementById('groq-api-key').value;
    const groqModel = document.getElementById('groq-model').value;
    const maxFiles = document.getElementById('max-files').value;
    const outputLang = document.getElementById('output-language').value;
    const githubToken = document.getElementById('github-token').value;

    frappe.call({
        method: 'git_analyze.api.save_settings',
        args: {
            groq_api_key: groqKey,
            groq_model: groqModel,
            max_files_limit: maxFiles,
            output_language: outputLang,
            github_token: githubToken
        },
        callback: function(r) {
            frappe.show_alert({
                message: 'Settings saved successfully',
                indicator: 'green'
            });
        },
        error: function(r) {
            frappe.msgprint({
                title: 'Error',
                indicator: 'red',
                message: r.message || 'Failed to save settings'
            });
        }
    });
};

git_analyzer.filterResults = function(filter) {
    document.querySelectorAll('.ga-result-card').forEach(function(card) {
        if (filter === 'all' || card.dataset.status === filter) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
};

git_analyzer.searchResults = function(query) {
    const q = query.toLowerCase();
    document.querySelectorAll('.ga-result-card').forEach(function(card) {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(q) ? 'block' : 'none';
    });
};

function exportAnalysis(name) {
    frappe.call({
        method: 'git_analyze.api.export_as_markdown',
        args: { analysis_name: name },
        callback: function(r) {
            if (r.message) {
                const blob = new Blob([r.message], { type: 'text/markdown' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = name + '.md';
                a.click();
                URL.revokeObjectURL(url);
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', git_analyzer.init);
