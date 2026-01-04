import streamlit as st
import datetime
import uuid

# --- 設定 ---
st.set_page_config(page_title="Git Command Simulator", layout="wide")

# --- CSSスタイル (ターミナル風) ---
st.markdown("""
<style>
    /* 全体の背景とフォント */
    .stApp {
        background-color: #1e1e1e;
        color: #ffffff;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* ターミナル出力エリア */
    .terminal-output {
        background-color: #000000;
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
    
    /* 入力エリア */
    .stTextArea textarea {
        background-color: #0d0d0d;
        color: #00ff00;
        font-family: 'Courier New', Courier, monospace;
        border: 1px solid #333;
    }
    
    /* サイドバー */
    [data-testid="stSidebar"] {
        background-color: #252526;
        color: #cccccc;
    }
    
    /* ボタン */
    .stButton button {
        background-color: #0e639c;
        color: white;
        border: none;
    }
    .stButton button:hover {
        background-color: #1798eb;
    }
</style>
""", unsafe_allow_html=True)

# --- ステート管理 (Gitシミュレーションロジック) ---
class GitSimulator:
    def __init__(self):
        self.initialized = False
        self.files = set() # ワーキングディレクトリのファイル
        self.index = set() # ステージングエリア
        self.commits = []  # コミット履歴 [{'id': str, 'message': str, 'timestamp': str, 'files': set}]
        self.history = []  # コミットログ表示用
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
        
        # git init
        if cmd == "git" and len(parts) > 1 and parts[1] == "init":
            self.initialized = True
            self.files = set()
            self.index = set()
            self.commits = []
            self.log_output(cmd_str, "Initialized empty Git repository in /project/.git/")
            return

        # reset (全リセット)
        if cmd == "reset":
            self.__init__()
            return

        # check initialization
        if not self.initialized:
            self.log_output(cmd_str, "fatal: not a git repository (or any of the parent directories): .git")
            return

        # touch filename
        if cmd == "touch":
            if len(parts) < 2:
                self.log_output(cmd_str, "usage: touch <filename>")
                return
            filename = parts[1]
            if filename not in self.files:
                self.files.add(filename)
                self.log_output(cmd_str, "") # touch usually has no output
            else:
                self.log_output(cmd_str, "") # update timestamp simulation
            return

        # git commands
        if cmd == "git":
            if len(parts) < 2:
                self.log_output(cmd_str, "usage: git <command>")
                return
            
            subcmd = parts[1]

            # git status
            if subcmd == "status":
                status_msg = f"On branch main\n"
                
                # Changes to be committed (staged)
                if self.index:
                    status_msg += "Changes to be committed:\n  (use \"git restore --staged <file>...\" to unstage)\n"
                    for f in self.index:
                        status_msg += f"\tnew file:   {f}\n"
                
                # Untracked files
                untracked = self.files - self.index - {f for c in self.commits for f in c['files']}
                # シンプル化: コミット済みファイルもfilesに残るが、変更検知は簡易化のため省略
                # ここでは「ステージされていないファイル」＝「Untracked」として簡易表示
                # 本来は tracked modified もあるが、シミュレーターなのでシンプルに
                
                current_committed = set()
                if self.commits:
                    current_committed = self.commits[-1]['files']
                
                # Untracked = 存在するが、Indexにも前回のCommitにもない
                # Modified = 前回のCommitにあるが、Commit時と異なり、かつIndexにない (今回は簡易化のためtouchで作ったものは作成or更新扱い)
                
                not_staged = self.files - self.index
                # 単純化: ステージされていないものはすべて Untracked or Modified 表示
                if not_staged:
                    status_msg += "\nUntracked files:\n  (use \"git add <file>...\" to include in what will be committed)\n"
                    for f in not_staged:
                         status_msg += f"\t{f}\n"

                if not self.index and not not_staged:
                     status_msg += "nothing to commit, working tree clean"
                
                self.log_output(cmd_str, status_msg)

            # git add
            elif subcmd == "add":
                if len(parts) < 3:
                     self.log_output(cmd_str, "nothing specified, nothing added.")
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

            # git commit
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

                # Commit
                commit_id = str(uuid.uuid4())[:7]
                new_commit = {
                    'id': commit_id,
                    'message': message,
                    'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'files': self.index.copy()
                }
                self.commits.append(new_commit)
                # Index is cleared after commit? git keeps tracked files in index roughly, but for adds...
                # 簡易シミュレータ: コミットしたらステージングは「クリーン」とみなす
                # ただしファイルは残る
                # 次回のstatusのために、indexはリセットするが、tracked情報は本来必要
                # ここでは簡易的に index を空にする (次の変更が必要)
                staged_count = len(self.index)
                self.index = set() 
                
                self.log_output(cmd_str, f"[{'main'} {commit_id}] {message}\n {staged_count} file(s) changed")

            # git log
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
                self.log_output(cmd_str, f"git: '{subcmd}' is not a git command. See 'git --help'.")
        else:
             self.log_output(cmd_str, f"{cmd}: command not found")

# --- セッション初期化 ---
if 'sim' not in st.session_state:
    st.session_state.sim = GitSimulator()

sim = st.session_state.sim

# --- UI構築 ---
st.title("Git Command Simulator")
st.caption("Gitの基本的なコマンドを練習できるシミュレーターです。")

# 2カラムレイアウト (サイドバー相当をcol1, メインをcol2にするか、st.sidebarを使うか)
# user request: サイドバーにリポジトリ状態表示
with st.sidebar:
    st.header("Repository Status")
    
    st.subheader("📁 Working Directory")
    if sim.files:
        for f in sim.files:
            st.code(f, language="text")
    else:
        st.write("(empty)")

    st.subheader("📋 Staging Area (Index)")
    if sim.index:
        for f in sim.index:
            st.markdown(f"<span style='color:#0f0'>✅ {f}</span>", unsafe_allow_html=True)
    else:
        st.write("(empty)")

    st.subheader("📜 Commit History (Latest 5)")
    if sim.commits:
        for c in reversed(sim.commits[-5:]):
            st.text(f"[{c['id']}] {c['message']}")
    else:
        st.write("(No commits yet)")

    st.divider()
    if st.button("Reset Simulator"):
        sim.run_command("reset")
        st.rerun()

# メインエリア
command = st.text_area("Command Input", height=100, placeholder="Example: git init, touch file.txt, git status...")

if st.button("実行 (Run)"):
    if command:
        commands = command.split('\n')
        for cmd in commands:
            if cmd.strip():
                sim.run_command(cmd)
        st.rerun()

# 結果表示
st.subheader("Terminal Output")
output_text = "\n".join(sim.terminal_log)
# 常に最下部を表示するためにJavaScriptを使う方法もあるが、ここでは簡易的にMarkdownで表示
# コンテナの高さを固定し、スクロールさせるCSSは適用済み
st.markdown(f'<div class="terminal-output">{output_text}</div>', unsafe_allow_html=True)

# ヒント
with st.expander("使い方 / Supported Commands"):
    st.markdown("""
    - `git init`: リポジトリを初期化
    - `touch <filename>`: ファイルを作成
    - `git status`: 状態を確認
    - `git add <file>` OR `git add .`: ステージング
    - `git commit -m "message"`: コミット
    - `git log --oneline`: 履歴を表示
    - `reset`: 最初からやり直す
    """)
