#!/usr/bin/env python3
"""
Forgejo Gradio Pages サービス（デバッグ版）
複数リポジトリのGradioアプリを動的に管理・デプロイ
"""

import os
import json
import subprocess
import threading
import time
from datetime import datetime
from flask import Flask, request, jsonify, Response
import docker
import requests
import logging
from pathlib import Path
import shutil
import socket

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ForgejoGradioManager:
    def __init__(self):
        try:
            self.docker_client = docker.from_env()
            logger.info("✅ Docker client connected successfully")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Docker: {e}")
            self.docker_client = None
            
        self.forgejo_url = os.getenv('FORGEJO_URL', 'http://server:3000')
        self.forgejo_token = os.getenv('FORGEJO_TOKEN', '')
        self.apps = {}
        self.port_start = int(os.getenv('GRADIO_PORT_START', 9100))  # デフォルトを9100に変更
        self.port_end = int(os.getenv('GRADIO_PORT_END', 9150))     # デフォルトを9150に変更
        self.app_dir = '/tmp/gradio-apps'
        
        logger.info(f"🔧 Port range: {self.port_start}-{self.port_end}")
        
        # ディレクトリ作成
        os.makedirs(self.app_dir, exist_ok=True)
        logger.info(f"📁 App directory created: {self.app_dir}")
        
        self.load_apps_state()
        
        # 既存コンテナのクリーンアップ
        self.cleanup_existing_containers()
        
    def cleanup_existing_containers(self):
        """既存のGradioコンテナをクリーンアップ"""
        if not self.docker_client:
            return
            
        try:
            logger.info("🧹 Cleaning up existing Gradio containers...")
            containers = self.docker_client.containers.list(all=True)
            
            for container in containers:
                if container.name.startswith('gradio-'):
                    try:
                        logger.info(f"🗑️  Removing container: {container.name}")
                        container.remove(force=True)
                    except Exception as e:
                        logger.warning(f"Failed to remove container {container.name}: {e}")
                        
            # アプリ状態をクリア
            self.apps.clear()
            self.save_apps_state()
            logger.info("✅ Container cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def is_port_available(self, port):
        """ポートが利用可能かチェック"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return True
        except OSError:
            return False

    def load_apps_state(self):
        """アプリ状態をロード"""
        try:
            state_file = '/data/apps_state.json'
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    saved_data = json.load(f)
                    for repo_id, app_info in saved_data.items():
                        self.apps[repo_id] = app_info
                logger.info(f"📊 Loaded {len(self.apps)} apps state")
        except Exception as e:
            logger.error(f"Error loading apps state: {e}")
            
    def save_apps_state(self):
        """アプリ状態を保存"""
        try:
            os.makedirs('/data', exist_ok=True)
            save_data = {}
            for repo_id, app_info in self.apps.items():
                save_data[repo_id] = {
                    'port': app_info.get('port'),
                    'status': app_info.get('status'),
                    'created': app_info.get('created'),
                    'last_updated': app_info.get('last_updated'),
                    'repo_full_name': app_info.get('repo_full_name'),
                    'branch': app_info.get('branch')
                }
            with open('/data/apps_state.json', 'w') as f:
                json.dump(save_data, f, indent=2)
            logger.info("💾 Apps state saved")
        except Exception as e:
            logger.error(f"Error saving apps state: {e}")

    def clone_repository(self, repo_full_name, branch='main'):
        """リポジトリをクローン（タイムアウト付き）"""
        try:
            logger.info(f"🔄 Cloning {repo_full_name}:{branch}")
            repo_dir = os.path.join(self.app_dir, repo_full_name.replace('/', '-'), branch)
            
            # 既存ディレクトリを削除
            if os.path.exists(repo_dir):
                shutil.rmtree(repo_dir)
                logger.info(f"🗑️  Removed existing directory: {repo_dir}")
            
            # 親ディレクトリ作成
            os.makedirs(os.path.dirname(repo_dir), exist_ok=True)
            
            # クローン（タイムアウト付き）
            clone_url = f"{self.forgejo_url}/{repo_full_name}.git"
            logger.info(f"🌐 Clone URL: {clone_url}")
            
            # Git clone with timeout
            result = subprocess.run([
                'git', 'clone', 
                '-b', branch,
                '--depth', '1',
                '--single-branch',
                clone_url, 
                repo_dir
            ], check=True, timeout=60, capture_output=True, text=True)
            
            logger.info(f"✅ Clone successful: {repo_dir}")
            
            # ファイル確認
            files = os.listdir(repo_dir)
            logger.info(f"📁 Repository files: {files}")
            
            return repo_dir
        except subprocess.TimeoutExpired:
            logger.error(f"⏰ Clone timeout for {repo_full_name}")
            return None
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Clone failed for {repo_full_name}: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"❌ Clone error for {repo_full_name}: {e}")
            return None

    def build_docker_image(self, repo_dir, repo_full_name, branch):
        """Dockerイメージをビルド"""
        if not self.docker_client:
            logger.error("❌ Docker client not available")
            return None
            
        try:
            dockerfile_path = os.path.join(repo_dir, 'Dockerfile')
            if not os.path.exists(dockerfile_path):
                logger.error(f"❌ Dockerfile not found in {repo_dir}")
                return None
            
            # イメージ名
            image_name = f"gradio-{repo_full_name.replace('/', '-').lower()}-{branch}"
            logger.info(f"🔨 Building Docker image: {image_name}")
            
            # ビルド
            image, build_logs = self.docker_client.images.build(
                path=repo_dir,
                tag=image_name,
                rm=True,
                forcerm=True
            )
            
            logger.info(f"✅ Build successful: {image_name}")
            return image_name
            
        except Exception as e:
            logger.error(f"❌ Build error: {e}")
            return None

    def get_available_port(self):
        """利用可能なポートを取得（改良版）"""
        # 現在使用中のポートを確認
        used_ports = {app.get('port') for app in self.apps.values() if app.get('port')}
        logger.info(f"🔍 Currently used ports: {used_ports}")
        
        for port in range(self.port_start, self.port_end + 1):
            if port not in used_ports and self.is_port_available(port):
                logger.info(f"✅ Found available port: {port}")
                return port
                
        logger.error(f"❌ No available ports in range {self.port_start}-{self.port_end}")
        return None

    def deploy_app(self, repo_full_name, branch='main'):
        """アプリをデプロイ（改良版）"""
        logger.info(f"🚀 Starting deployment: {repo_full_name}:{branch}")
        
        if not self.docker_client:
            return False, "Docker client not available"
            
        try:
            repo_id = f"{repo_full_name}:{branch}"
            
            # 既存アプリを停止
            if repo_id in self.apps:
                logger.info(f"🛑 Stopping existing app: {repo_id}")
                self.stop_app(repo_id)
            
            # リポジトリクローン
            repo_dir = self.clone_repository(repo_full_name, branch)
            if not repo_dir:
                return False, "Failed to clone repository"
            
            # 必須ファイルの確認
            required_files = ['Dockerfile', 'app.py', 'requirements.txt']
            for file in required_files:
                file_path = os.path.join(repo_dir, file)
                if not os.path.exists(file_path):
                    logger.error(f"❌ Required file missing: {file}")
                    return False, f"Required file missing: {file}"
                logger.info(f"✅ Found required file: {file}")
            
            # Dockerイメージビルド
            image_name = self.build_docker_image(repo_dir, repo_full_name, branch)
            if not image_name:
                return False, "Failed to build Docker image"
            
            # ポート取得
            port = self.get_available_port()
            if not port:
                return False, "No available ports"
            
            logger.info(f"🔌 Using port: {port}")
            
            # コンテナ起動
            container_name = f"gradio-{repo_full_name.replace('/', '-')}-{branch}".lower()
            
            # 既存コンテナを削除
            try:
                old_container = self.docker_client.containers.get(container_name)
                old_container.remove(force=True)
                logger.info(f"🗑️  Removed old container: {container_name}")
            except docker.errors.NotFound:
                pass
            
            # 新しいコンテナを起動
            logger.info(f"🐳 Starting container: {container_name}")
            
            container = self.docker_client.containers.run(
                image_name,
                name=container_name,
                ports={'7860/tcp': port},
                environment={
                    'GRADIO_SERVER_NAME': '0.0.0.0',
                    'GRADIO_SERVER_PORT': '7860',
                    'GRADIO_ROOT_PATH': f'/{repo_full_name}'
                },
                detach=True,
                restart_policy={'Name': 'unless-stopped'}
                # ネットワーク指定を削除 - デフォルトネットワークを使用
            )
            
            # アプリ情報を保存
            self.apps[repo_id] = {
                'container': container,
                'port': port,
                'status': 'running',
                'created': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat(),
                'image': image_name,
                'repo_full_name': repo_full_name,
                'branch': branch
            }
            
            self.save_apps_state()
            
            logger.info(f"🎉 Successfully deployed {repo_id} on port {port}")
            return True, f"App deployed successfully on port {port}"
            
        except Exception as e:
            logger.error(f"❌ Deployment error for {repo_full_name}: {e}")
            return False, str(e)

    def stop_app(self, repo_id):
        """アプリを停止"""
        try:
            if repo_id in self.apps:
                container = self.apps[repo_id].get('container')
                if container:
                    try:
                        container.remove(force=True)
                        logger.info(f"🗑️  Removed container: {container.name}")
                    except Exception as e:
                        logger.warning(f"Failed to remove container: {e}")
                del self.apps[repo_id]
                self.save_apps_state()
                logger.info(f"🛑 Stopped app: {repo_id}")
                return True
        except Exception as e:
            logger.error(f"Error stopping app {repo_id}: {e}")
        return False

    def get_app_port(self, repo_full_name, branch='main'):
        """アプリのポートを取得"""
        repo_id = f"{repo_full_name}:{branch}"
        if repo_id in self.apps:
            app_info = self.apps[repo_id]
            if app_info.get('status') == 'running':
                return app_info.get('port')
        return None

    def list_apps(self):
        """アプリ一覧を取得"""
        return {
            repo_id: {
                'port': info.get('port'),
                'status': info.get('status'),
                'created': info.get('created'),
                'last_updated': info.get('last_updated'),
                'repo_full_name': info.get('repo_full_name'),
                'branch': info.get('branch')
            }
            for repo_id, info in self.apps.items()
        }

    def health_check(self):
        """ヘルスチェック"""
        healthy_apps = 0
        for repo_id, app_info in self.apps.items():
            try:
                container = app_info.get('container')
                if container:
                    container.reload()
                    if container.status == 'running':
                        healthy_apps += 1
                        app_info['status'] = 'running'
                    else:
                        app_info['status'] = 'stopped'
                else:
                    app_info['status'] = 'stopped'
            except Exception as e:
                logger.error(f"Health check failed for {repo_id}: {e}")
                app_info['status'] = 'error'
        
        return {
            'total_apps': len(self.apps),
            'healthy_apps': healthy_apps,
            'timestamp': datetime.now().isoformat(),
            'port_range': f"{self.port_start}-{self.port_end}"
        }

# Flask アプリケーション
app = Flask(__name__)
manager = ForgejoGradioManager()

def proxy_to_gradio_app(repo_full_name, path, branch='main'):
    """Gradioアプリにプロキシ"""
    port = manager.get_app_port(repo_full_name, branch)
    if not port:
        return f"<h1>404 - Gradio App Not Found</h1><p>App '{repo_full_name}' is not deployed or not running.</p><p><a href='/'>← Back to Apps List</a></p>", 404
    
    try:
        target_url = f"http://192.168.0.131:{port}{path}"
        
        if request.method == 'GET':
            resp = requests.get(target_url, params=request.args, timeout=30)
        elif request.method == 'POST':
            resp = requests.post(target_url, 
                               data=request.get_data(),
                               headers={'Content-Type': request.content_type},
                               timeout=30)
        else:
            resp = requests.request(request.method, target_url, 
                                  data=request.get_data(),
                                  headers={'Content-Type': request.content_type},
                                  timeout=30)
        
        return Response(resp.content, status=resp.status_code, headers=dict(resp.headers))
        
    except Exception as e:
        logger.error(f"Proxy error for {repo_full_name}: {e}")
        return f"<h1>502 - Service Unavailable</h1><p>Error connecting to Gradio app: {str(e)}</p>", 502

@app.route('/<username>/<repository>/')
@app.route('/<username>/<repository>/<path:path>')
def serve_gradio_app(username, repository, path=''):
    """Gradioアプリを提供（パスベース）"""
    repo_full_name = f"{username}/{repository}"
    if not path.startswith('/'):
        path = '/' + path
    return proxy_to_gradio_app(repo_full_name, path)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Forgejo Webhookエンドポイント"""
    try:
        logger.info("📧 Received webhook")
        data = request.get_json()
        
        if data.get('action') == 'push' or request.headers.get('X-Forgejo-Event') == 'push':
            repo_full_name = data.get('repository', {}).get('full_name')
            ref = data.get('ref', 'refs/heads/main')
            branch = ref.replace('refs/heads/', '')
            
            if repo_full_name:
                logger.info(f"🔄 Processing push event for {repo_full_name}:{branch}")
                
                def deploy_async():
                    success, message = manager.deploy_app(repo_full_name, branch)
                    logger.info(f"📊 Deploy result for {repo_full_name}: {message}")
                
                threading.Thread(target=deploy_async, daemon=True).start()
                
                return jsonify({
                    'status': 'accepted',
                    'message': f'Deployment started for {repo_full_name}:{branch}'
                }), 202
        
        return jsonify({'status': 'ignored', 'message': 'Event not handled'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/apps', methods=['GET'])
def list_apps():
    """アプリ一覧API"""
    logger.info("📋 Listing apps")
    return jsonify(manager.list_apps())

@app.route('/api/apps/<path:repo_full_name>', methods=['POST'])
def deploy_app(repo_full_name):
    """手動デプロイAPI"""
    try:
        logger.info(f"🚀 Manual deploy request for {repo_full_name}")
        data = request.get_json() or {}
        branch = data.get('branch', 'main')
        
        # バックグラウンドでデプロイ
        def deploy_async():
            success, message = manager.deploy_app(repo_full_name, branch)
            logger.info(f"📊 Deploy result: {message}")
        
        threading.Thread(target=deploy_async, daemon=True).start()
        
        return jsonify({
            'status': 'accepted',
            'message': f'Deployment started for {repo_full_name}:{branch}'
        }), 202
        
    except Exception as e:
        logger.error(f"Deploy API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/apps/<path:repo_full_name>', methods=['DELETE'])
def stop_app(repo_full_name):
    """アプリ停止API"""
    try:
        data = request.get_json() or {}
        branch = data.get('branch', 'main')
        repo_id = f"{repo_full_name}:{branch}"
        
        if manager.stop_app(repo_id):
            return jsonify({'status': 'success', 'message': 'App stopped'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to stop app'}), 400
            
    except Exception as e:
        logger.error(f"Stop API error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """ヘルスチェックAPI"""
    return jsonify(manager.health_check())

@app.route('/')
def index():
    """ステータスページ"""
    apps = manager.list_apps()
    health_status = manager.health_check()
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🚀 Forgejo Gradio Pages (Debug)</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .app {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; }}
            .status-running {{ background-color: #d4edda; }}
            .status-stopped {{ background-color: #f8d7da; }}
            .status-error {{ background-color: #fff3cd; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
            .url {{ font-family: monospace; background: #f8f9fa; padding: 5px; border-radius: 3px; }}
            .debug {{ background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🚀 Forgejo Gradio Pages (Debug)</h1>
            <p>GitHub Pagesライクな Gradio アプリ デプロイサービス</p>
            <p><strong>Active Apps:</strong> {health_status['healthy_apps']} / {health_status['total_apps']}</p>
            <p><strong>Port Range:</strong> {health_status['port_range']}</p>
        </div>
        
        <div class="debug">
            <h3>🔧 Debug Info</h3>
            <p><strong>Docker:</strong> {'✅ Connected' if manager.docker_client else '❌ Not connected'}</p>
            <p><strong>Forgejo URL:</strong> {manager.forgejo_url}</p>
            <p><strong>Token:</strong> {'✅ Set' if manager.forgejo_token else '❌ Not set'}</p>
            <p><strong>Port Range:</strong> {manager.port_start}-{manager.port_end}</p>
        </div>
        
        <h2>📱 Deployed Gradio Apps</h2>
        {''.join([f'''
            <div class="app status-{app_info['status']}">
                <h3>{app_info['repo_full_name']}</h3>
                <p><strong>Status:</strong> {app_info['status']}</p>
                <p><strong>Port:</strong> {app_info['port']}</p>
                <p><strong>URL:</strong> <a href="/{app_info['repo_full_name']}/" target="_blank" class="url">/{app_info['repo_full_name']}/</a></p>
                <p><strong>Direct:</strong> <a href="http://192.168.0.131:{app_info['port']}" target="_blank" class="url">192.168.0.131:{app_info['port']}</a></p>
                <p><strong>Branch:</strong> {app_info['branch']}</p>
                <p><strong>Created:</strong> {app_info['created']}</p>
            </div>
        ''' for repo_id, app_info in apps.items()]) if apps else '<p>No apps deployed yet.</p>'}
        
        <h2>🧪 Test Deploy</h2>
        <button onclick="testDeploy()">Test Deploy Sunwood-ai-labs/gradio-pages</button>
        <div id="testResult"></div>
        
        <script>
        function testDeploy() {{
            fetch('/api/apps/Sunwood-ai-labs/gradio-pages', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{'branch': 'main'}})
            }})
            .then(response => response.json())
            .then(data => {{
                document.getElementById('testResult').innerHTML = 
                    '<p><strong>Result:</strong> ' + JSON.stringify(data) + '</p>';
            }})
            .catch(error => {{
                document.getElementById('testResult').innerHTML = 
                    '<p><strong>Error:</strong> ' + error + '</p>';
            }});
        }}
        </script>
        
        <h2>📝 API Test</h2>
        <ul>
            <li><a href="/api/apps">GET /api/apps</a></li>
            <li><a href="/health">GET /health</a></li>
        </ul>
    </body>
    </html>
    """
    return html

if __name__ == '__main__':
    logger.info("🚀 Starting Forgejo Gradio Pages (Debug version)")
    app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
