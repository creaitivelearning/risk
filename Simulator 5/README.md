 (cd "$(git rev-parse --show-toplevel)" && git apply --3way <<'EOF' 
diff --git a/README.md b/README.md
index a8fd1f4..5c41ed1 100644
--- a/README.md
+++ b/README.md
@@ -1 +1 @@
-# risk
\ No newline at end of file
+# risk
diff --git a/Simulator 5/README.md b/Simulator 5/README.md
index e352dee..7c2dc19 100644
--- a/Simulator 5/README.md	
+++ b/Simulator 5/README.md	
@@ -1,3 +1,11 @@
 # Risk Simulator
 
-A game of Risk with AI-controlled characters.
\ No newline at end of file
+A game of Risk with AI-controlled characters.
+
+## Running the Simulator
+
+Execute the main script from the repository root:
+
+```bash
+python "Simulator 5/main.py"
+```
diff --git a/Simulator 5/__init__.py b/Simulator 5/__init__.py
new file mode 100644
index 0000000..e69de29
 
EOF
)
