import streamlit as st
import datetime
import uuid

# --- 設定 ---
st.set_page_config(page_title="Git Command Simulator", layout="wide", initial_sidebar_state="collapsed")

# --- セッションステート初期化 ---
if 'page' not in st.session_state:
    st.session_state.page = 'landing'  # 'landing' or 'simulator'
if 'sim' not in st.session_state:
    # Simulatorクラス定義後に初期化するため、ここはプレースホルダー
    pass

# --- CSS (デザイン調整) ---
st.markdown("""
<style>
    /* 全体のフォント調整 */
    .stApp {
        font-family: "Helvetica Neue", Arial, sans-serif;
    }
    /* 説明ページのカード風デザイン */
    .instruction-card {
        background-color: #f0f2f6; 
        padding: 20px; 
        border-radius: 10px; 
        border-left: 5px solid #ff4b4b;
        margin-bottom: 20px;
    }
    /* ダークモード対応 */
    @media (prefers-color-scheme: dark) {
        .instruction-card {
            background-color: #262730;
        }
    }
    
    /* ターミナル出力エリア (シミュレータ用) */
    .terminal-output {
        background-color: #0e1117;
        color: #00ff00;
        padding: 15px;
        border-radius: 5px;
        font-family: 'Courier New', Courier, monospace;
        white-space: pre-wrap;
        border: 1px solid #333;
        margin-bottom: 20px;
        height: 300px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# --- ページ遷移関数 ---
def go_to_simulator():
    st.session_state.page = 'simulator'
    # st.rerun() はボタンのコールバック内では不要な場合もあるが念のため

def go_to_landing():
    st.session_state.page = 'landing'

# --- Git Simulator Class (変更なし、再利用) ---
class GitSimulator:
    def __init__(self):
        self.initialized = False
        self.files = set() 
        self.index = set() 
        self.commits = [] 
        self.terminal_log = ["Welcome to Git Simulator! Type 'git init' to start."]

    def log_output(self, command, result):
        self.terminal_log.append(f"$ {command}")
        if result:
            self.terminal_log.append(result)

    def run_command(self, cmd_str):
        parts = cmd_str.strip().split()
        if not parts:
            return
        cmd = parts[0]
        
        if cmd == "git" and len(parts) > 1 and parts[1] == "init":
            self.initialized = True
            self.files = set()
            self.index = set()
            self.commits = []
            self.log_output(cmd_str, "Initialized empty Git repository in /project/.git/")
            return

        if cmd == "reset":
            self.__init__()
            return

        if not self.initialized:
            self.log_output(cmd_str, "fatal: not a git repository (or any of the parent directories): .git")
            return

        if cmd == "touch":
            if len(parts) < 2:
                self.log_output(cmd_str, "usage: touch <filename>")
                return
            filename = parts[1]
            if filename not in self.files:
                self.files.add(filename)
                self.log_output(cmd_str, "") 
            else:
                self.log_output(cmd_str, "") 
            return

        if cmd == "git":
            if len(parts) < 2:
                self.log_output(cmd_str, "usage: git <command>")
                return
            subcmd = parts[1]

            if subcmd == "status":
                status_msg = f"On branch main\n"
                if self.index:
                    status_msg += "Changes to be committed:\n"
                    for f in self.index:
                        status_msg += f"\tnew file:   {f}\n"
                
                not_staged = self.files - self.index
                if not_staged:
                    status_msg += "\nUntracked files:\n"
                    for f in not_staged:
                         status_msg += f"\t{f}\n"

                if not self.index and not not_staged:
                     status_msg += "nothing to commit, working tree clean"
                self.log_output(cmd_str, status_msg)

            elif subcmd == "add":
                if len(parts) < 3:
                     self.log_output(cmd_str, "nothing specified")
                     return
                target = parts[2]
                if target == ".":
                    for f in self.files:
                        self.index.add(f)
                else:
                    if target in self.files:
                        self.index.add(target)
                    else:
                        self.log_output(cmd_str, f"fatal: pathspec '{target}' did not match any files")
                        return
                self.log_output(cmd_str, "")

            elif subcmd == "commit":
                if "-m" not in parts:
                    self.log_output(cmd_str, "error: command 'commit' requires -m option")
                    return
                try:
                    m_index = parts.index("-m")
                    message = " ".join(parts[m_index+1:]).strip('"').strip("'")
                except IndexError:
                     self.log_output(cmd_str, "error: switch `m` requires a value")
                     return

                if not self.index:
                    self.log_output(cmd_str, "nothing to commit, working tree clean")
                    return

                commit_id = str(uuid.uuid4())[:7]
                new_commit = {
                    'id': commit_id,
                    'message': message,
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'files': self.index.copy()
                }
                self.commits.append(new_commit)
                staged_count = len(self.index)
                self.index = set() 
                self.log_output(cmd_str, f"[{'main'} {commit_id}] {message}\n {staged_count} file(s) changed")

            elif subcmd == "log":
                if "--oneline" in parts:
                    log_str = ""
                    for c in reversed(self.commits):
                        log_str += f"{c['id']} {c['message']}\n"
                    self.log_output(cmd_str, log_str.strip())
                else:
                    log_str = ""
                    for c in reversed(self.commits):
                        log_str += f"commit {c['id']}\nDate:   {c['timestamp']}\n\n    {c['message']}\n\n"
                    self.log_output(cmd_str, log_str.strip())
            else:
                self.log_output(cmd_str, f"git: '{subcmd}' is not a git command.")
        else:
             self.log_output(cmd_str, f"{cmd}: command not found")

# --- Initialize Simulator Instance ---
if isinstance(st.session_state.get('sim'), dict) or 'sim' not in st.session_state:
    st.session_state.sim = GitSimulator()
sim = st.session_state.sim


# ==========================================
#  ページ表示ロジック
# ==========================================

if st.session_state.page == 'landing':
    # --- ランディングページ (説明画面) ---
    st.title("Git Command Simulator 🚀")
    
    st.markdown("""
    ### ようこそ！
    ここでは、安全な環境でGitの基本コマンドを練習することができます。
    実際のファイルを操作することなく、ブラウザ上でGitの動きをシミュレーションします。
    """)

    st.markdown('<div class="instruction-card">', unsafe_allow_html=True)
    st.markdown("""
    #### 📚 学べること
    1. **リポジトリの初期化**: `git init`
    2. **ファイルの作成**: `touch filename`
    3. **変更の確認**: `git status`
    4. **ステージング**: `git add .`
    5. **コミット**: `git commit -m "message"`
    6. **履歴の確認**: `git log`
    """)
    st.markdown('</div>', unsafe_allow_html=True)

    st.warning("⚠️ 注意: これはシミュレーターです。実際のGitHubには接続されません。")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # 中央寄せするためのカラム配置
        if st.button("シミュレーターを起動する (Start)", type="primary", use_container_width=True):
            go_to_simulator()
            st.rerun()

elif st.session_state.page == 'simulator':
    # --- シミュレーターページ ---
    
    # Navigation to go back
    if st.button("← Back to Home"):
        go_to_landing()
        st.rerun()

    st.title("Git Terminal")
    st.caption("コマンドを入力して実行ボタンを押してください。")

    # Layout
    with st.sidebar:
        st.header("Repository Status")
        
        st.subheader("📁 Working Directory")
        if sim.files:
            for f in sim.files:
                st.code(f, language="text")
        else:
            st.write("(empty)")

        st.subheader("📋 Staging Area")
        if sim.index:
            for f in sim.index:
                st.markdown(f"<span style='color:#0f0'>✅ {f}</span>", unsafe_allow_html=True)
        else:
            st.write("(empty)")

        st.subheader("📜 Commit History")
        if sim.commits:
            for c in reversed(sim.commits[-5:]):
                st.text(f"[{c['id']}] {c['message']}")
        else:
            st.write("(No commits yet)")
        
        st.divider()
        if st.button("Reset All"):
            sim.run_command("reset")
            st.rerun()

    # Main Interface
    command = st.text_area("Command Input ($)", height=85, placeholder="git init...")

    if st.button("実行 (Run Command)", type="primary"):
        if command:
            commands = command.split('\n')
            for cmd in commands:
                if cmd.strip():
                     sim.run_command(cmd)
            st.rerun()

    st.subheader("Terminal Output")
    output_text = "\n".join(sim.terminal_log)
    st.markdown(f'<div class="terminal-output">{output_text}</div>', unsafe_allow_html=True)
