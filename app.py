import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")

conn = psycopg2.connect(DATABASE_URL)
cursor = conn.cursor()

"""IT Agent Web Application"""
from flask import Flask, render_template_string, jsonify, request, render_template, redirect, url_for, flash, make_response
from flask_cors import CORS
from src.agent.it_agent import AssetManager
from src.utils.assets import AssetStore
import json
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from src.utils.config import Config
from src.utils.email_notifier import EmailNotifier
from src.utils.user_store import UserStore
import secrets
import random
import string
import csv
import io

app = Flask(__name__)
# Secure the app
app.secret_key = Config().get('auth.secret_key', secrets.token_hex(16))
CORS(app)

# Setup Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User Model
class User(UserMixin):
    def __init__(self, id, role='viewer'):
        self.id = id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    user_data = user_store.get_user(user_id)
    if user_data:
        return User(user_id, role=user_data.get('role', 'viewer'))
    return None

# Access control decorator
def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Administrator access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Login Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        config = Config()
        valid_user = config.get('auth.username', 'admin')
        valid_pass = config.get('auth.password', 'admin123')
        
        if username and password:
            user_data = user_store.validate_user(username, password)
            if user_data:
                login_user(User(username, role=user_data.get('role', 'viewer')))
                return redirect(url_for('index'))
            
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        config = Config()
        valid_user = config.get('auth.username', 'admin')
        
        if username == valid_user:
            # Generate new random password
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            new_password = ''.join(random.choice(chars) for _ in range(12))
            
            # Update password in UserStore
            if user_store.update_password(username, new_password):
                # Send email
                notifier = EmailNotifier()
                user_email = config.get('email.username') or config.get('email.sender_email')
                
                if notifier.send_password_reset(user_email, new_password):
                    flash('Password reset successful! Check your email for the new password.', 'success')
                else:
                    flash(f'Password reset successful! Email failed. Your new password is: {new_password}', 'success')
                    print(f"\n[RESET] New password for {username}: {new_password}\n")
            else:
                flash('Error updating password.', 'error')
        else:
            # Don't reveal user existence
            flash('If the username exists, a reset email has been sent.', 'success')
            
        return redirect(url_for('login'))
        
    return render_template('forgot_password.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Initialize agent, stores
agent = AssetManager()
agent.start()
asset_store = AssetStore()
user_store = UserStore()

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Draup Asset Management - Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-bottom: 20px; text-align: center; }
        .header h1 { color: #667eea; font-size: 2.5em; margin-bottom: 10px; }
        .header p { color: #666; font-size: 1.1em; }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; justify-content: center; flex-wrap: wrap; }
        .tab-button { padding: 10px 20px; border-radius: 20px; border: none; cursor: pointer; background: rgba(255,255,255,0.2); color: #fff; font-weight: 600; transition: all 0.2s; }
        .tab-button.active { background: #fff; color: #667eea; box-shadow: 0 6px 18px rgba(0,0,0,0.15); }
        .dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
        .card h2 { color: #667eea; margin-bottom: 15px; font-size: 1.5em; }
        .status-badge { display: inline-block; padding: 8px 16px; border-radius: 20px; font-weight: bold; margin: 5px 0; }
        .status-healthy { background: #4caf50; color: white; }
        .status-degraded { background: #ff9800; color: white; }
        .status-error { background: #f44336; color: white; }
        .btn { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px; margin: 5px; transition: all 0.3s; }
        .btn:hover { background: #764ba2; transform: translateY(-2px); box-shadow: 0 5px 15px rgba(0,0,0,0.2); }
        .btn-success { background: #4caf50; }
        .task-list { list-style: none; }
        .task-item { padding: 15px; margin: 10px 0; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #667eea; }
        .task-item h3 { color: #333; margin-bottom: 5px; }
        .task-item p { color: #666; font-size: 0.9em; }
        .results { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); margin-top: 20px; display: none; }
        .results.show { display: block; }
        .results pre { background: #f8f9fa; padding: 15px; border-radius: 8px; overflow-x: auto; max-height: 500px; overflow-y: auto; }
        .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .metric { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
        .metric:last-child { border-bottom: none; }
        .metric-label { font-weight: bold; color: #333; }
        .metric-value { color: #667eea; }
        /* Asset table */
        .asset-layout { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1.4fr); gap: 20px; }
        .asset-table { width: 100%; border-collapse: collapse; font-size: 0.9em; }
        .asset-table th, .asset-table td { padding: 8px 10px; border-bottom: 1px solid #eee; text-align: left; }
        .asset-table th { background: #f5f6ff; color: #555; position: sticky; top: 0; z-index: 1; }
        .asset-table tbody tr:hover { background: #f8f9ff; }
        .badge { display: inline-block; padding: 3px 8px; border-radius: 999px; font-size: 0.75em; }
        .badge-inuse { background: #e3f5e5; color: #2e7d32; }
        .badge-instock { background: #e3f2fd; color: #1565c0; }
        .badge-retired { background: #fbe9e7; color: #d84315; }
        .badge-repair { background: #fff8e1; color: #f9a825; }
        .asset-actions button { padding: 4px 10px; font-size: 0.75em; margin-right: 4px; }
        .btn-danger { background: #f44336; }
        .btn-small { padding: 6px 10px; font-size: 0.8em; }
        .form-group { margin-bottom: 10px; }
        .form-group label { display: block; font-size: 0.85em; font-weight: 600; margin-bottom: 4px; color: #555; }
        .form-group input, .form-group select, .form-group textarea { width: 100%; padding: 8px 10px; border-radius: 6px; border: 1px solid #ddd; font-size: 0.9em; }
        .form-row { display: flex; gap: 10px; }
        .form-row .form-group { flex: 1; }
        .asset-summary { display: flex; gap: 12px; margin-bottom: 10px; flex-wrap: wrap; }
        .asset-filters { display: flex; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; align-items: center; }
        .asset-filters input, .asset-filters select { padding: 6px 8px; border-radius: 999px; border: 1px solid #ddd; font-size: 0.8em; }
        .asset-filters label { font-size: 0.8em; color: #555; }
        .chip { background: #f5f5f5; border-radius: 999px; padding: 4px 10px; font-size: 0.8em; color: #555; }
        .section-hidden { display: none; }
        .section-visible { display: block; }
        /* Modal */
        .modal { display: none; position: fixed; z-index: 1000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.5); }
        .modal-content { background-color: #fefefe; margin: 10% auto; padding: 25px; border: 1px solid #888; width: 60%; max-width: 800px; border-radius: 15px; position: relative; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
        .close-btn { color: #aaa; float: right; font-size: 28px; font-weight: bold; cursor: pointer; }
        .close-btn:hover { color: black; }
        .detail-row { display: flex; border-bottom: 1px solid #eee; padding: 10px 0; }
        .detail-label { font-weight: bold; width: 180px; color: #555; }
        .detail-value { flex: 1; color: #333; }
        .modal-actions { margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; text-align: right; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header" style="position: relative;">
            <div style="position: absolute; top: 20px; right: 20px; display: flex; align-items: center; gap: 10px;">
                 <span style="color: #555; font-weight: 600;">👤 {{ current_user.id }}</span>
                 <a href="/logout" class="btn" style="padding: 8px 15px; font-size: 0.9em; text-decoration: none; margin: 0;">Logout</a>
            </div>
            <h1>🖥️ Draup Asset Management</h1>
        </div>
        <div class="tabs">
            <button class="tab-button active" id="tab-assets" onclick="showSection('assets')">IT Assets</button>
            {% if current_user.role == 'admin' %}
            <button class="tab-button" id="tab-users" onclick="showSection('users')">Users</button>
            {% endif %}
        </div>


        <!-- IT Assets section -->
        <div id="section-assets" class="section-visible">
            <div class="card">
                <h2>IT Assets</h2>
                <div class="asset-layout">
                    <div>
                        <div class="asset-summary" id="asset-summary">
                            <!-- Summary chips will be populated by JS -->
                        </div>
                        <div class="asset-filters">
                            <label>
                                Search:
                                <input id="asset-filter-search" placeholder="Laptop model, owner, location, tag..." oninput="applyAssetFilters()" />
                            </label>
                            <label>
                                Status:
                                <select id="asset-filter-status" onchange="applyAssetFilters()">
                                    <option value="">All</option>
                                    <option>In Use</option>
                                    <option>In Stock</option>
                                    <option>Retired</option>
                                    <option>Repair</option>
                                </select>
                            </label>
                            <label>
                                Type:
                                    <select id="asset-filter-type" onchange="applyAssetFilters()">
                                    <option value="">All</option>
                                    <option>Desktop</option>
                                    <option>Laptop</option>
                                    <option>Mac</option>
                                    <option>Server</option>
                                    <option>Network Device</option>
                                    <option>Printer</option>
                                    <option>Mobile</option>
                                    <option>TV</option>
                                    <option>Software License</option>
                                    <option>Other</option>
                                </select>
                            </label>
                            <label>
                                Department:
                                <input id="asset-filter-dept" placeholder="e.g. IT" oninput="applyAssetFilters()" />
                            </label>
                            <button class="btn btn-small" onclick="downloadReport()" style="margin-left: auto;">⬇ Download Report</button>
                        </div>
                        <div style="max-height: 380px; overflow: auto; border-radius: 10px; border: 1px solid #eee;">
                            <table class="asset-table" id="asset-table">
                                <thead>
                                    <tr>
                                        <th>Model</th>
                                        <th>Type</th>
                                        <th>Owner</th>
                                        <th>Emp Code</th>
                                        <th>Status</th>
                                        <th>Location</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="asset-tbody">
                                    <!-- Filled by JS -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div>
                        <h3 style="margin-bottom:10px; color:#444;">{% if current_user.role == 'admin' %}Add / Edit Asset{% else %}Add IT Asset{% endif %}</h3>
                        <form id="asset-form" onsubmit="submitAssetForm(event)">
                            <input type="hidden" id="asset-id" />
                            <div class="form-group">
                                <label for="asset-name">Laptop Model *</label>
                                <input id="asset-name" required placeholder="e.g. XPS 13, ThinkPad T14" />
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="asset-type">Type *</label>
                                    <select id="asset-type" required>
                                        <option value="">Select type</option>
                                        <option>Desktop</option>
                                        <option>Laptop</option>
                                        <option>Mac</option>
                                        <option>Server</option>
                                        <option>Network Device</option>
                                        <option>Printer</option>
                                        <option>Mobile</option>
                                        <option>TV</option>
                                        <option>Software License</option>
                                        <option>Other</option>
                                    </select>
                                </div>
                                <div class="form-group">
                                    <label for="asset-status">Status</label>
                                    <select id="asset-status">
                                        <option>In Use</option>
                                        <option>In Stock</option>
                                        <option>Retired</option>
                                        <option>Repair</option>
                                    </select>
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="asset-owner">Owner</label>
                                    <input id="asset-owner" placeholder="Person or team" />
                                </div>
                                <div class="form-group">
                                    <label for="asset-owner-email">Owner Email</label>
                                    <input id="asset-owner-email" type="email" placeholder="owner@example.com" />
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="asset-employee">Employee Code</label>
                                <input id="asset-employee" placeholder="e.g. EMP12345" />
                            </div>
                            <div class="form-group">
                                <label for="asset-department">Department</label>
                                <input id="asset-department" placeholder="e.g. IT, Finance" />
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="asset-location">Location</label>
                                    <input id="asset-location" placeholder="Office / Rack / Floor" />
                                </div>
                                <div class="form-group">
                                    <label for="asset-serial">Laptop Serial Number</label>
                                    <input id="asset-serial" placeholder="Laptop serial number" />
                                </div>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="asset-purchase">Purchase Date</label>
                                    <input id="asset-purchase" type="date" />
                                </div>
                                <div class="form-group">
                                    <label for="asset-warranty">Warranty Expiry</label>
                                    <input id="asset-warranty" type="date" />
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="asset-config">Configuration</label>
                                <textarea id="asset-config" placeholder="e.g. i5 / 16GB RAM / 512GB SSD / Windows 11" rows="2"></textarea>
                            </div>
                            <div class="form-group">
                                <label for="asset-accessories">Accessories</label>
                                <input id="asset-accessories" placeholder="e.g. Mouse, Keyboard, Monitor" />
                            </div>
                            <div class="form-group">
                                <label for="asset-invoice">Invoice Reference</label>
                                <input id="asset-invoice" placeholder="e.g. INV-2025-001 or URL" />
                            </div>
                            <div class="form-group">
                                <label for="asset-tags">Tags</label>
                                <input id="asset-tags" placeholder="Comma-separated (e.g. critical,remote)" />
                            </div>
                            <div style="margin-top: 10px;">
                                <button type="submit" class="btn btn-small btn-success" id="asset-submit-btn">Save Asset</button>
                                <button type="button" class="btn btn-small" onclick="resetAssetForm()">Clear</button>
                                <button type="button" class="btn btn-small btn-danger" id="asset-delete-btn" style="display:none;" onclick="deleteFromForm()">Delete</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>

        {% if current_user.role == 'admin' %}
        <!-- Users Management section -->
        <div id="section-users" class="section-hidden">
            <div class="card">
                <h2>User Management</h2>
                <div class="asset-layout">
                    <div>
                        <div style="max-height: 480px; overflow: auto; border-radius: 10px; border: 1px solid #eee;">
                            <table class="asset-table" id="user-table">
                                <thead>
                                    <tr>
                                        <th>Username</th>
                                        <th>Role</th>
                                        <th>Created At</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="user-tbody">
                                    <!-- Filled by JS -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div>
                        <h3 style="margin-bottom:10px; color:#444;">Create New User</h3>
                        <form id="user-form" onsubmit="submitUserForm(event)">
                            <div class="form-group">
                                <label for="user-username">Username *</label>
                                <input id="user-username" required placeholder="Enter username" />
                            </div>
                            <div class="form-group">
                                <label for="user-password">Password *</label>
                                <input id="user-password" type="password" required placeholder="Enter password" />
                            </div>
                            <div class="form-group">
                                <label for="user-role">Role *</label>
                                <select id="user-role" required>
                                    <option value="viewer">View-only access</option>
                                    <option value="admin">Administrator access</option>
                                </select>
                            </div>
                            <div style="margin-top: 10px;">
                                <button type="submit" class="btn btn-small btn-success">Create User</button>
                                <button type="reset" class="btn btn-small">Clear</button>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        {% endif %}
        
        <!-- View Asset Modal -->
        <div id="view-modal" class="modal">
            <div class="modal-content">
                <span class="close-btn" onclick="closeModal()">&times;</span>
                <h2 id="modal-title" style="margin-bottom: 20px; color: #667eea;">Asset Details</h2>
                <div id="modal-details"></div>
                <div class="modal-actions" id="modal-actions"></div>
    </div>
    <script>
        const userRole = '{{ current_user.role }}';
        // ----------- Tabs -----------
        function showSection(section) {
            const assets = document.getElementById('section-assets');
            const users = document.getElementById('section-users');
            const tabAssets = document.getElementById('tab-assets');
            const tabUsers = document.getElementById('tab-users');

            // Hide all
            assets.className = 'section-hidden';
            if(users) users.className = 'section-hidden';
            tabAssets.classList.remove('active');
            if(tabUsers) tabUsers.classList.remove('active');

            if (section === 'assets') {
                assets.className = 'section-visible';
                tabAssets.classList.add('active');
                loadAssets();
            } else if (section === 'users') {
                if(users) {
                    users.className = 'section-visible';
                    tabUsers.classList.add('active');
                    loadUsers();
                }
            }
        }

        async function apiCall(endpoint, method = 'GET', data = null) {
            try {
                const options = { method: method, headers: {'Content-Type': 'application/json'} };
                if (data) options.body = JSON.stringify(data);
                const response = await fetch(`/api/${endpoint}`, options);
                return await response.json();
            } catch (error) { return { error: error.message }; }
        }
        async function refreshHealth() {
            const statusDiv = document.getElementById('health-status');
            statusDiv.innerHTML = '<div class="loading"></div> Loading...';
            const health = await apiCall('health');
            if (health.error) { statusDiv.innerHTML = `<p style="color: red;">Error: ${health.error}</p>`; return; }
            const status = health.overall_status || 'unknown';
            const statusClass = status === 'healthy' ? 'status-healthy' : status === 'degraded' ? 'status-degraded' : 'status-error';
            let html = `<div class="status-badge ${statusClass}">${status.toUpperCase()}</div><div style="margin-top: 15px;">`;
            if (health.checks) {
                for (const [checkName, checkData] of Object.entries(health.checks)) {
                    const checkStatus = checkData.status || 'unknown';
                    const checkClass = checkStatus === 'healthy' ? 'status-healthy' : checkStatus === 'degraded' ? 'status-degraded' : 'status-error';
                    html += `<div style="margin: 5px 0;"><strong>${checkName}:</strong> <span class="status-badge ${checkClass}">${checkStatus}</span></div>`;
                }
            }
            html += '</div>';
            statusDiv.innerHTML = html;
        }
        async function refreshMetrics() {
            const metricsDiv = document.getElementById('metrics');
            metricsDiv.innerHTML = '<div class="loading"></div> Loading...';
            const metrics = await apiCall('metrics');
            if (metrics.error) { metricsDiv.innerHTML = `<p style="color: red;">Error: ${metrics.error}</p>`; return; }
            let html = '';
            html += `<div class="metric"><span class="metric-label">Uptime:</span><span class="metric-value">${Math.floor(metrics.uptime_seconds || 0)}s</span></div>`;
            html += `<div class="metric"><span class="metric-label">Tasks Completed:</span><span class="metric-value">${metrics.tasks_completed || 0}</span></div>`;
            html += `<div class="metric"><span class="metric-label">Tasks Failed:</span><span class="metric-value">${metrics.tasks_failed || 0}</span></div>`;
            html += `<div class="metric"><span class="metric-label">Success Rate:</span><span class="metric-value">${((metrics.success_rate || 0) * 100).toFixed(1)}%</span></div>`;
            html += `<div class="metric"><span class="metric-label">Errors:</span><span class="metric-value">${(metrics.errors || []).length}</span></div>`;
            metricsDiv.innerHTML = html;
        }
        async function loadTasks() {
            const taskList = document.getElementById('task-list');
            taskList.innerHTML = '<li>Loading...</li>';
            const data = await apiCall('tasks');
            if (data.error) { taskList.innerHTML = `<li style="color: red;">Error: ${data.error}</li>`; return; }
            if (data.tasks && data.tasks.length > 0) {
                taskList.innerHTML = data.tasks.map(task => `<li class="task-item"><h3>${task.name}</h3><p>${task.description}</p><button class="btn" onclick="executeTask('${task.name}')" style="margin-top: 10px;">Execute</button></li>`).join('');
            } else { taskList.innerHTML = '<li>No tasks available</li>'; }
        }
        async function executeTask(taskName) {
            showResults(`Executing task: ${taskName}...`);
            const result = await apiCall('execute', 'POST', {task_name: taskName, params: {}});
            showResults(JSON.stringify(result, null, 2));
            refreshMetrics();
        }
        async function runDiagnostic() {
            showResults('Running full diagnostic... This may take a moment.');
            const results = await apiCall('diagnose', 'POST');
            showResults(JSON.stringify(results, null, 2));
            refreshHealth();
            refreshMetrics();
        }
        function showResults(content) {
            const resultsDiv = document.getElementById('results');
            const contentDiv = document.getElementById('results-content');
            contentDiv.textContent = content;
            resultsDiv.classList.add('show');
            resultsDiv.scrollIntoView({ behavior: 'smooth' });
        }
        function refreshAll() { refreshHealth(); refreshMetrics(); loadTasks(); }

        // ----------- Assets ----------
        let allAssets = [];
        function statusBadgeClass(status) {
            if (!status) return 'badge-inuse';
            const s = status.toLowerCase();
            if (s.includes('stock')) return 'badge-instock';
            if (s.includes('retired')) return 'badge-retired';
            if (s.includes('repair')) return 'badge-repair';
            return 'badge-inuse';
        }

        async function loadAssets() {
            const tbody = document.getElementById('asset-tbody');
            tbody.innerHTML = '<tr><td colspan="6">Loading assets...</td></tr>';
            const data = await apiCall('assets');
            if (data.error) {
                tbody.innerHTML = `<tr><td colspan="6" style="color:red;">Error: ${data.error}</td></tr>`;
                return;
            }
            allAssets = data.assets || [];
            applyAssetFilters();
        }

        function applyAssetFilters() {
            const tbody = document.getElementById('asset-tbody');
            const search = (document.getElementById('asset-filter-search')?.value || '').toLowerCase();
            const status = document.getElementById('asset-filter-status')?.value || '';
            const type = document.getElementById('asset-filter-type')?.value || '';
            const dept = (document.getElementById('asset-filter-dept')?.value || '').toLowerCase();

            if (!allAssets.length) {
                tbody.innerHTML = '<tr><td colspan="6">No assets yet. Use the form to add one.</td></tr>';
                updateAssetSummary(allAssets);
                return;
            }

            const filtered = allAssets.filter(asset => {
                const aStatus = (asset.status || '');
                const aType = (asset.asset_type || '');
                const aDept = (asset.department || '');
                const haystack = [
                    asset.name || '',
                    asset.owner || '',
                    asset.owner_email || '',
                    asset.employee_code || '',
                    asset.location || '',
                    asset.tags || '',
                    asset.serial_number || '',
                    asset.accessories || '',
                    asset.invoice || ''
                ].join(' ').toLowerCase();

                if (status && aStatus !== status) return false;
                if (type && aType !== type) return false;
                if (dept && !aDept.toLowerCase().includes(dept)) return false;
                if (search && !haystack.includes(search)) return false;
                return true;
            });

            if (!filtered.length) {
                tbody.innerHTML = '<tr><td colspan="6">No assets match the selected filters.</td></tr>';
            } else {
                tbody.innerHTML = filtered.map(asset => {
                    const badgeCls = statusBadgeClass(asset.status);
                    return `<tr>
                        <td>${asset.name || ''}</td>
                        <td>${asset.asset_type || ''}</td>
                        <td>${asset.owner || ''}</td>
                        <td>${asset.employee_code || ''}</td>
                        <td><span class="badge ${badgeCls}">${asset.status || ''}</span></td>
                        <td>${asset.location || ''}</td>
                        <td class="asset-actions">
                            <button class="btn btn-small" onclick='viewAsset(${JSON.stringify(asset)})'>View</button>
                            ${userRole === 'admin' ? `<button class="btn btn-small" onclick='editAsset(${JSON.stringify(asset)})'>Edit</button>` : ''}
                        </td>
                    </tr>`;
                }).join('');
            }

            updateAssetSummary(filtered);
        }

        function updateAssetSummary(assets) {
            const summaryDiv = document.getElementById('asset-summary');
            if (!assets || !assets.length) {
                summaryDiv.innerHTML = '';
                return;
            }
            const total = assets.length;
            const byStatus = assets.reduce((acc, a) => {
                const s = (a.status || 'In Use');
                acc[s] = (acc[s] || 0) + 1;
                return acc;
            }, {});
            const byType = assets.reduce((acc, a) => {
                const t = (a.asset_type || 'Unknown');
                acc[t] = (acc[t] || 0) + 1;
                return acc;
            }, {});

            const laptopCount = byType['Laptop'] || 0;
            const macCount = byType['Mac'] || 0;

            summaryDiv.innerHTML = `
                <span class="chip">Total Assets: ${total}</span>
                <span class="chip">Laptops: ${laptopCount}</span>
                <span class="chip">Mac: ${macCount}</span>
                ${Object.keys(byStatus).map(s => `<span class="chip">${s}: ${byStatus[s]}</span>`).join('')}
            `;
        }

        function resetAssetForm() {
            document.getElementById('asset-id').value = '';
            document.getElementById('asset-name').value = '';
            document.getElementById('asset-type').value = '';
            document.getElementById('asset-status').value = 'In Use';
            document.getElementById('asset-owner').value = '';
            document.getElementById('asset-owner-email').value = '';
            document.getElementById('asset-employee').value = '';
            document.getElementById('asset-department').value = '';
            document.getElementById('asset-location').value = '';
            document.getElementById('asset-serial').value = '';
            document.getElementById('asset-purchase').value = '';
            document.getElementById('asset-warranty').value = '';
            document.getElementById('asset-config').value = '';
            document.getElementById('asset-accessories').value = '';
            document.getElementById('asset-invoice').value = '';
            document.getElementById('asset-tags').value = '';
            document.getElementById('asset-submit-btn').textContent = 'Save Asset';
            const deleteBtn = document.getElementById('asset-delete-btn');
            if (deleteBtn) deleteBtn.style.display = 'none';
        }

        function viewAsset(asset) {
            const modal = document.getElementById('view-modal');
            const details = document.getElementById('modal-details');
            const actions = document.getElementById('modal-actions');
            const fields = [
                { k: 'id', l: 'Asset ID' },
                { k: 'name', l: 'Model Name' },
                { k: 'asset_type', l: 'Type' },
                { k: 'status', l: 'Status' },
                { k: 'owner', l: 'Owner' },
                { k: 'owner_email', l: 'Owner Email' },
                { k: 'employee_code', l: 'Employee Code' },
                { k: 'department', l: 'Department' },
                { k: 'location', l: 'Location' },
                { k: 'serial_number', l: 'Serial Number' },
                { k: 'purchase_date', l: 'Purchase Date' },
                { k: 'warranty_expiry', l: 'Warranty Expiry' },
                { k: 'configuration', l: 'Configuration' },
                { k: 'accessories', l: 'Accessories' },
                { k: 'invoice', l: 'Invoice' },
                { k: 'tags', l: 'Tags' },
                { k: 'created_at', l: 'Created At' },
                { k: 'updated_at', l: 'Updated At' }
            ];
            
            let html = '';
            fields.forEach(f => {
                const val = asset[f.k] || '-';
                let displayVal = val;
                if (f.k === 'status') {
                     const badgeCls = statusBadgeClass(val);
                     displayVal = `<span class="badge ${badgeCls}">${val}</span>`;
                }
                html += `<div class="detail-row"><div class="detail-label">${f.l}</div><div class="detail-value">${displayVal}</div></div>`;
            });
            
            details.innerHTML = html;
            
            if (actions) {
                let actionHtml = '';
                if (userRole === 'admin') {
                    actionHtml += `
                        <button class="btn btn-small" onclick='closeModal(); editAsset(${JSON.stringify(asset)})'>Edit</button>
                        <button class="btn btn-small btn-danger" onclick="closeModal(); deleteAsset('${asset.id}')">Delete</button>
                    `;
                }
                actionHtml += `<button class="btn btn-small" onclick="closeModal()">Close</button>`;
                actions.innerHTML = actionHtml;
            }
            
            modal.style.display = 'block';
        }

        function closeModal() {
            document.getElementById('view-modal').style.display = 'none';
        }
        
        window.onclick = function(event) {
            const modal = document.getElementById('view-modal');
            if (event.target == modal) {
                modal.style.display = "none";
            }
        }

        function editAsset(asset) {
            document.getElementById('asset-id').value = asset.id || '';
            document.getElementById('asset-name').value = asset.name || '';
            document.getElementById('asset-type').value = asset.asset_type || '';
            document.getElementById('asset-status').value = asset.status || 'In Use';
            document.getElementById('asset-status').value = asset.status || 'In Use';
            document.getElementById('asset-owner').value = asset.owner || '';
            document.getElementById('asset-owner-email').value = asset.owner_email || '';
            document.getElementById('asset-employee').value = asset.employee_code || '';
            document.getElementById('asset-department').value = asset.department || '';
            document.getElementById('asset-location').value = asset.location || '';
            document.getElementById('asset-serial').value = asset.serial_number || '';
            document.getElementById('asset-purchase').value = asset.purchase_date || '';
            document.getElementById('asset-warranty').value = asset.warranty_expiry || '';
            document.getElementById('asset-config').value = asset.configuration || '';
            document.getElementById('asset-accessories').value = asset.accessories || '';
            document.getElementById('asset-invoice').value = asset.invoice || '';
            document.getElementById('asset-tags').value = asset.tags || '';
            document.getElementById('asset-submit-btn').textContent = 'Update Asset';
            
            // Show delete button
            const deleteBtn = document.getElementById('asset-delete-btn');
            if (deleteBtn) {
                deleteBtn.style.display = 'inline-block';
                // Remove previous onclick to prevent closures stacking if not careful, 
                // but direct assignment is fine.
                // We need to pass ID to deleteFromForm
                deleteBtn.setAttribute('data-id', asset.id);
            }

            // Switch to Assets tab when editing
            showSection('assets');
        }
        
        async function deleteFromForm() {
             const id = document.getElementById('asset-delete-btn').getAttribute('data-id') || document.getElementById('asset-id').value;
             if (id) {
                 if(confirm('Are you sure you want to delete this asset?')) {
                    const res = await apiCall(`assets/${id}`, 'DELETE');
                    if (res.success) {
                        loadAssets();
                        resetAssetForm();
                    } else {
                        alert('Failed to delete asset: ' + (res.error || 'Unknown error'));
                    }
                 }
             }
        }

        async function deleteAsset(id) {
            if (!confirm('Delete this asset?')) return;
            const res = await apiCall(`assets/${id}`, 'DELETE');
            if (res.success) {
                loadAssets();
            } else {
                alert('Failed to delete asset: ' + (res.error || 'Unknown error'));
            }
        }

        function downloadReport() {
            window.location.href = '/api/assets/export';
        }

        async function submitAssetForm(event) {
            event.preventDefault();
            const id = document.getElementById('asset-id').value;
            const payload = {
                name: document.getElementById('asset-name').value,
                asset_type: document.getElementById('asset-type').value,
                status: document.getElementById('asset-status').value,
                owner: document.getElementById('asset-owner').value,
                owner_email: document.getElementById('asset-owner-email').value,
                employee_code: document.getElementById('asset-employee').value,
                department: document.getElementById('asset-department').value,
                location: document.getElementById('asset-location').value,
                serial_number: document.getElementById('asset-serial').value,
                purchase_date: document.getElementById('asset-purchase').value,
                warranty_expiry: document.getElementById('asset-warranty').value,
                configuration: document.getElementById('asset-config').value,
                tags: document.getElementById('asset-tags').value,
                accessories: document.getElementById('asset-accessories').value,
                invoice: document.getElementById('asset-invoice').value,
            };
            let res;
            if (id) {
                res = await apiCall(`assets/${id}`, 'PUT', payload);
            } else {
                res = await apiCall('assets', 'POST', payload);
            }
            if (res.error || res.success === false) {
                alert('Failed to save asset: ' + (res.error || 'Unknown error'));
                return;
            }
            resetAssetForm();
            // Reload list and keep current filters
            loadAssets();
        }

        // ----------- Users ----------
        async function loadUsers() {
            const tbody = document.getElementById('user-tbody');
            if(!tbody) return;
            tbody.innerHTML = '<tr><td colspan="4">Loading users...</td></tr>';
            const data = await apiCall('users');
            if (data.error) {
                tbody.innerHTML = `<tr><td colspan="4" style="color:red;">Error: ${data.error}</td></tr>`;
                return;
            }
            const users = data.users || [];
            if (!users.length) {
                tbody.innerHTML = '<tr><td colspan="4">No users found.</td></tr>';
            } else {
                tbody.innerHTML = users.map(user => `
                    <tr>
                        <td>${user.username}</td>
                        <td><span class="badge ${user.role === 'admin' ? 'badge-inuse' : 'badge-instock'}">${user.role}</span></td>
                        <td>${user.created_at ? new Date(user.created_at).toLocaleString() : '-'}</td>
                        <td class="asset-actions">
                            ${user.username !== 'admin' ? `<button class="btn btn-small btn-danger" onclick="deleteUser('${user.username}')">Delete</button>` : '<em>System Admin</em>'}
                        </td>
                    </tr>
                `).join('');
            }
        }

        async function submitUserForm(event) {
            event.preventDefault();
            const payload = {
                username: document.getElementById('user-username').value,
                password: document.getElementById('user-password').value,
                role: document.getElementById('user-role').value
            };
            const res = await apiCall('users', 'POST', payload);
            if (res.error) {
                alert('Failed to create user: ' + res.error);
                return;
            }
            document.getElementById('user-form').reset();
            loadUsers();
        }

        async function deleteUser(username) {
            if (!confirm(`Delete user "${username}"?`)) return;
            const res = await apiCall(`users/${username}`, 'DELETE');
            if (res.success) {
                loadUsers();
            } else {
                alert('Failed to delete user: ' + (res.error || 'Unknown error'));
            }
        }

        window.addEventListener('DOMContentLoaded', function() {
            loadAssets();
        });
    </script>
</body>
</html>'''

@app.route('/')
@login_required
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/health', methods=['GET'])
@login_required
def get_health():
    """Get health status"""
    try:
        health = agent.get_health_status()
        return jsonify(health)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics', methods=['GET'])
@login_required
def get_metrics():
    """Get agent metrics"""
    try:
        metrics = agent.get_metrics()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    """Get available tasks"""
    try:
        tasks = [{'name': task.name, 'description': task.description} for task in agent.tasks]
        return jsonify({'tasks': tasks})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/execute', methods=['POST'])
@login_required
def execute_task():
    """Execute a task"""
    try:
        data = request.json
        task_name = data.get('task_name')
        params = data.get('params', {})
        
        result = agent.execute_task(task_name, **params)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/api/diagnose', methods=['POST'])
@login_required
def diagnose():
    """Run full diagnostic"""
    try:
        results = agent.diagnose()
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/history', methods=['GET'])
@login_required
def get_history():
    """Get task history"""
    try:
        limit = request.args.get('limit', 10, type=int)
        history = agent.get_task_history(limit=limit)
        return jsonify({'history': history})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/assets', methods=['GET'])
@login_required
def list_assets():
    """List all IT assets."""
    try:
        assets = asset_store.list_assets()
        return jsonify({'assets': assets})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/assets', methods=['POST'])
@login_required
def create_asset():
    """Create a new IT asset."""
    try:
        payload = request.json or {}
        if not payload.get('name') or not payload.get('asset_type'):
            return jsonify({'success': False, 'error': 'name and asset_type are required'}), 400
        asset = asset_store.create_asset(payload)
        return jsonify({'success': True, 'asset': asset})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/assets/<asset_id>', methods=['PUT'])
@login_required
@admin_required
def update_asset(asset_id: str):
    """Update an existing IT asset."""
    try:
        payload = request.json or {}
        updated = asset_store.update_asset(asset_id, payload)
        if not updated:
            return jsonify({'success': False, 'error': 'Asset not found'}), 404
        return jsonify({'success': True, 'asset': updated})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/assets/<asset_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_asset(asset_id: str):
    """Delete an IT asset."""
    try:
        ok = asset_store.delete_asset(asset_id)
        if not ok:
            return jsonify({'success': False, 'error': 'Asset not found'}), 404
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/assets/export', methods=['GET'])
@login_required
def export_assets():
    """Export assets as CSV."""
    try:
        assets = asset_store.list_assets()
        
        # Create CSV in memory
        si = io.StringIO()
        if assets:
            # Get all keys from the first asset (or a defined list of desired fields)
            # A defined list is safer to ensure order and avoid missing fields if the first asset is partial
            fieldnames = [
                "id", "name", "asset_type", "status", "owner", "owner_email", 
                "department", "location", "employee_code", "serial_number",
                "purchase_date", "warranty_expiry", "configuration", 
                "tags", "accessories", "invoice", "created_at", "updated_at"
            ]
            writer = csv.DictWriter(si, fieldnames=fieldnames)
            writer.writeheader()
            
            for asset in assets:
                # Filter/Clean asset dict to only have known fields
                row = {k: asset.get(k, '') for k in fieldnames}
                writer.writerow(row)
        else:
             writer = csv.writer(si)
             writer.writerow(["No assets found"])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=assets_report.csv"
        output.headers["Content-type"] = "text/csv"
        return output
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# User Management APIs
@app.route('/api/users', methods=['GET'])
@login_required
@admin_required
def list_users():
    """List all users (Admin only)"""
    return jsonify({'success': True, 'users': user_store.list_users()})

@app.route('/api/users', methods=['POST'])
@login_required
@admin_required
def create_user_api():
    """Create a new user (Admin only)"""
    try:
        data = request.json or {}
        username = data.get('username')
        password = data.get('password')
        role = data.get('role', 'viewer')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
            
        user = user_store.create_user(username, password, role)
        if user:
            return jsonify({'success': True, 'user': user})
        return jsonify({'success': False, 'error': 'User already exists'}), 409
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users/<username>', methods=['DELETE'])
@login_required
@admin_required
def delete_user_api(username):
    """Delete a user (Admin only)"""
    try:
        if user_store.delete_user(username):
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': 'Could not delete user'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    import sys
    config = Config()
    port = config.get('server.port', 8080)
    
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
        
    # Avoid emojis here to prevent UnicodeEncodeError on some Windows terminals
    print("\nIT Agent Web Application starting...")
    print(f"Open your browser at: http://127.0.0.1:{port}")
    print("\nPress Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

