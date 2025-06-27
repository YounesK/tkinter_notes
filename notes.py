import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import tkinter.font as tkFont
import sqlite3
import random
import string

DB_NAME = 'gestion_notes.db'

# --- Base de données ---

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        role TEXT CHECK(role IN ('admin', 'prof', 'etudiant')),
        mot_de_passe TEXT NOT NULL
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS modules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS inscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        etudiant_id INTEGER,
        module_id INTEGER,
        FOREIGN KEY(etudiant_id) REFERENCES utilisateurs(id),
        FOREIGN KEY(module_id) REFERENCES modules(id)
    )""")
    c.execute("""
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        etudiant_id INTEGER,
        module_id INTEGER,
        prof_id INTEGER,
        note_normale REAL,
        note_rattrapage REAL,
        FOREIGN KEY(etudiant_id) REFERENCES utilisateurs(id),
        FOREIGN KEY(module_id) REFERENCES modules(id),
        FOREIGN KEY(prof_id) REFERENCES utilisateurs(id)
    )""")
    # Créer un admin par défaut si pas existant
    c.execute("SELECT * FROM utilisateurs WHERE role='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO utilisateurs (nom, role, mot_de_passe) VALUES (?, 'admin', ?)",
                  ('admin', 'admin123'))
    # Comptes profs par défaut
    default_profs = [
        ('prof_jules', 'pass123'),
        ('prof_marie', 'pass123'),
        ('prof_pierre', 'pass123')
    ]
    c.execute("SELECT * FROM utilisateurs WHERE role='prof'")
    if not c.fetchone():
        for nom, pwd in default_profs:
            c.execute("INSERT INTO utilisateurs (nom, role, mot_de_passe) VALUES (?, 'prof', ?)", (nom, pwd))
    conn.commit()
    conn.close()

def get_conn_cursor():
    conn = sqlite3.connect(DB_NAME)
    return conn, conn.cursor()

# --- Fonctions utilitaires ---

def hash_password(pwd):
    # Pour simplifier, on stocke en clair (à améliorer)
    return pwd

def verify_password(stored, provided):
    return stored == provided

def random_name(prefix, length=6):
    return prefix + ''.join(random.choices(string.ascii_lowercase, k=length))

# --- Application Tkinter ---

class GestionNotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestion de Notes")
        self.user = None

        # Police personnalisée
        self.default_font_size = 12
        self.font = tkFont.Font(family="Helvetica", size=self.default_font_size)

        self.build_login()

    def build_login(self):
        self.clear_root()
        tk.Label(self.root, text="Login", font=self.font).grid(row=0, column=0)
        tk.Label(self.root, text="Mot de passe", font=self.font).grid(row=1, column=0)
        self.entry_login = tk.Entry(self.root, font=self.font)
        self.entry_login.grid(row=0, column=1)
        self.entry_pwd = tk.Entry(self.root, show="*", font=self.font)
        self.entry_pwd.grid(row=1, column=1)
        tk.Button(self.root, text="Se connecter", command=self.login, font=self.font).grid(row=2, column=0, columnspan=2)

    def login(self):
        login = self.entry_login.get()
        pwd = self.entry_pwd.get()
        conn, c = get_conn_cursor()
        c.execute("SELECT id, nom, role, mot_de_passe FROM utilisateurs WHERE nom=?", (login,))
        row = c.fetchone()
        conn.close()
        if row and verify_password(row[3], pwd):
            self.user = {'id': row[0], 'nom': row[1], 'role': row[2]}
            messagebox.showinfo("Succès", f"Connecté en tant que {self.user['role']}")
            if self.user['role'] == 'admin':
                self.build_admin_interface()
            elif self.user['role'] == 'prof':
                self.build_prof_interface()
            else:
                self.build_etudiant_interface()
        else:
            messagebox.showerror("Erreur", "Login ou mot de passe incorrect")

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    # --- Interface Admin ---

    def build_admin_interface(self):
        self.clear_root()
        tk.Label(self.root, text=f"Admin: {self.user['nom']}", font=self.font).grid(row=0, column=0, columnspan=5)

        tk.Button(self.root, text="Augmenter taille texte", command=self.increase_font, font=self.font).grid(row=0, column=5)
        tk.Button(self.root, text="Diminuer taille texte", command=self.decrease_font, font=self.font).grid(row=0, column=6)

        tk.Button(self.root, text="Créer étudiants aléatoires", command=self.create_random_students, font=self.font).grid(row=1, column=0)
        tk.Button(self.root, text="Créer profs aléatoires", command=self.create_random_profs, font=self.font).grid(row=1, column=1)
        tk.Button(self.root, text="Créer un module", command=self.create_module, font=self.font).grid(row=2, column=0)
        tk.Button(self.root, text="Attribuer module à étudiant", command=self.assign_module, font=self.font).grid(row=2, column=1)
        tk.Button(self.root, text="Consulter données", command=self.show_admin_data, font=self.font).grid(row=3, column=0, columnspan=2)
        tk.Button(self.root, text="Déconnexion", command=self.logout, font=self.font).grid(row=4, column=0, columnspan=3)

    def increase_font(self):
        self.default_font_size += 2
        self.font.configure(size=self.default_font_size)
        self.refresh_interface()

    def decrease_font(self):
        if self.default_font_size > 6:
            self.default_font_size -= 2
            self.font.configure(size=self.default_font_size)
            self.refresh_interface()

    def refresh_interface(self):
        if self.user:
            if self.user['role'] == 'admin':
                self.build_admin_interface()
            elif self.user['role'] == 'prof':
                self.build_prof_interface()
            else:
                self.build_etudiant_interface()

    def create_random_students(self):
        conn, c = get_conn_cursor()
        count = 100
        for _ in range(count):
            name = random_name('etu_')
            pwd = 'pass123'
            c.execute("INSERT INTO utilisateurs (nom, role, mot_de_passe) VALUES (?, 'etudiant', ?)", (name, pwd))
        conn.commit()
        conn.close()
        messagebox.showinfo("Succès", f"{count} étudiants créés")

    def create_random_profs(self):
        conn, c = get_conn_cursor()
        count = 10
        for _ in range(count):
            name = random_name('prof_')
            pwd = 'pass123'
            c.execute("INSERT INTO utilisateurs (nom, role, mot_de_passe) VALUES (?, 'prof', ?)", (name, pwd))
        conn.commit()
        conn.close()
        messagebox.showinfo("Succès", f"{count} professeurs créés")

    def create_module(self):
        module_name = simpledialog.askstring("Module", "Nom du module :")
        if module_name:
            conn, c = get_conn_cursor()
            c.execute("INSERT INTO modules (nom) VALUES (?)", (module_name,))
            conn.commit()
            conn.close()
            messagebox.showinfo("Succès", f"Module '{module_name}' créé")

    def assign_module(self):
        conn, c = get_conn_cursor()
        c.execute("SELECT id, nom FROM utilisateurs WHERE role='etudiant'")
        etudiants = c.fetchall()
        if not etudiants:
            messagebox.showerror("Erreur", "Aucun étudiant trouvé")
            conn.close()
            return
        c.execute("SELECT id, nom FROM modules")
        modules = c.fetchall()
        if not modules:
            messagebox.showerror("Erreur", "Aucun module trouvé")
            conn.close()
            return
        etu_names = [e[1] for e in etudiants]
        etu_choice = simpledialog.askstring("Etudiant", f"Choisissez un étudiant parmi : {', '.join(etu_names)}")
        if etu_choice not in etu_names:
            messagebox.showerror("Erreur", "Étudiant invalide")
            conn.close()
            return
        etu_id = [e[0] for e in etudiants if e[1] == etu_choice][0]
        mod_names = [m[1] for m in modules]
        mod_choice = simpledialog.askstring("Module", f"Choisissez un module parmi : {', '.join(mod_names)}")
        if mod_choice not in mod_names:
            messagebox.showerror("Erreur", "Module invalide")
            conn.close()
            return
        mod_id = [m[0] for m in modules if m[1] == mod_choice][0]
        c.execute("SELECT * FROM inscriptions WHERE etudiant_id=? AND module_id=?", (etu_id, mod_id))
        if c.fetchone():
            messagebox.showinfo("Info", "Étudiant déjà inscrit à ce module")
        else:
            c.execute("INSERT INTO inscriptions (etudiant_id, module_id) VALUES (?, ?)", (etu_id, mod_id))
            conn.commit()
            messagebox.showinfo("Succès", f"Module attribué à l'étudiant")
        conn.close()

    def show_admin_data(self):
        win = tk.Toplevel(self.root)
        win.title("Consultation des données")
        notebook = ttk.Notebook(win)
        notebook.pack(fill='both', expand=True)

        frame_profs = ttk.Frame(notebook)
        notebook.add(frame_profs, text="Enseignants")
        self.build_treeview(frame_profs, "prof")

        frame_etus = ttk.Frame(notebook)
        notebook.add(frame_etus, text="Étudiants")
        self.build_treeview(frame_etus, "etudiant")

        frame_notes = ttk.Frame(notebook)
        notebook.add(frame_notes, text="Notes")
        self.build_notes_treeview(frame_notes)

    def build_treeview(self, parent, role):
        cols = ('ID', 'Nom')
        tree = ttk.Treeview(parent, columns=cols, show='headings')
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        tree.pack(fill='both', expand=True)

        conn, c = get_conn_cursor()
        c.execute("SELECT id, nom FROM utilisateurs WHERE role=?", (role,))
        rows = c.fetchall()
        conn.close()

        for r in rows:
            tree.insert('', 'end', values=r)

    def build_notes_treeview(self, parent):
        cols = ('Étudiant', 'Module', 'Professeur', 'Note normale', 'Note rattrapage')
        tree = ttk.Treeview(parent, columns=cols, show='headings')
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        tree.pack(fill='both', expand=True)

        conn, c = get_conn_cursor()
        c.execute("""
            SELECT u_et.nom, m.nom, u_prof.nom, n.note_normale, n.note_rattrapage
            FROM notes n
            JOIN utilisateurs u_et ON n.etudiant_id = u_et.id
            JOIN modules m ON n.module_id = m.id
            JOIN utilisateurs u_prof ON n.prof_id = u_prof.id
        """)
        rows = c.fetchall()
        conn.close()

        for r in rows:
            tree.insert('', 'end', values=r)

    # --- Interface Professeur ---

    def build_prof_interface(self):
        self.clear_root()
        tk.Label(self.root, text=f"Professeur: {self.user['nom']}", font=self.font).grid(row=0, column=0, columnspan=2)
        tk.Button(self.root, text="Saisir/Modifier notes", command=self.prof_saisie_notes, font=self.font).grid(row=1, column=0)
        tk.Button(self.root, text="Déconnexion", command=self.logout, font=self.font).grid(row=2, column=0, columnspan=2)

    def prof_saisie_notes(self):
        self.clear_root()
        tk.Label(self.root, text="Saisie des notes", font=self.font).grid(row=0, column=0, columnspan=4)
        conn, c = get_conn_cursor()
        c.execute("SELECT id, nom FROM modules")
        modules = c.fetchall()
        if not modules:
            messagebox.showerror("Erreur", "Aucun module trouvé")
            conn.close()
            self.build_prof_interface()
            return
        mod_names = [m[1] for m in modules]
        mod_choice = simpledialog.askstring("Module", f"Choisissez un module parmi : {', '.join(mod_names)}")
        if mod_choice not in mod_names:
            messagebox.showerror("Erreur", "Module invalide")
            conn.close()
            self.build_prof_interface()
            return
        mod_id = [m[0] for m in modules if m[1] == mod_choice][0]
        c.execute("""SELECT u.id, u.nom FROM utilisateurs u
                     JOIN inscriptions i ON u.id = i.etudiant_id
                     WHERE i.module_id=?""", (mod_id,))
        etudiants = c.fetchall()
        if not etudiants:
            messagebox.showinfo("Info", "Aucun étudiant inscrit à ce module")
            conn.close()
            self.build_prof_interface()
            return
        self.entries = {}
        row = 1
        tk.Label(self.root, text="Étudiant", font=self.font).grid(row=row, column=0)
        tk.Label(self.root, text="Note normale", font=self.font).grid(row=row, column=1)
        tk.Label(self.root, text="Note rattrapage", font=self.font).grid(row=row, column=2)
        row += 1
        for etu_id, etu_nom in etudiants:
            tk.Label(self.root, text=etu_nom, font=self.font).grid(row=row, column=0)
            e_norm = tk.Entry(self.root, width=5, font=self.font)
            e_norm.grid(row=row, column=1)
            e_rattr = tk.Entry(self.root, width=5, font=self.font)
            e_rattr.grid(row=row, column=2)
            self.entries[etu_id] = (e_norm, e_rattr)
            c.execute("""SELECT note_normale, note_rattrapage FROM notes
                         WHERE etudiant_id=? AND module_id=? AND prof_id=?""",
                      (etu_id, mod_id, self.user['id']))
            note = c.fetchone()
            if note:
                e_norm.insert(0, str(note[0]) if note[0] is not None else '')
                e_rattr.insert(0, str(note[1]) if note[1] is not None else '')
            row += 1
        tk.Button(self.root, text="Enregistrer", command=lambda: self.save_notes(mod_id), font=self.font).grid(row=row, column=0, columnspan=3)
        tk.Button(self.root, text="Retour", command=self.build_prof_interface, font=self.font).grid(row=row+1, column=0, columnspan=3)
        conn.close()

    def save_notes(self, module_id):
        conn, c = get_conn_cursor()
        for etu_id, (e_norm, e_rattr) in self.entries.items():
            try:
                note_normale = float(e_norm.get()) if e_norm.get() else None
                note_rattrapage = float(e_rattr.get()) if e_rattr.get() else None
                c.execute("""SELECT id FROM notes WHERE etudiant_id=? AND module_id=? AND prof_id=?""",
                          (etu_id, module_id, self.user['id']))
                row = c.fetchone()
                if row:
                    c.execute("""UPDATE notes SET note_normale=?, note_rattrapage=? WHERE id=?""",
                              (note_normale, note_rattrapage, row[0]))
                else:
                    c.execute("""INSERT INTO notes (etudiant_id, module_id, prof_id, note_normale, note_rattrapage)
                                 VALUES (?, ?, ?, ?, ?)""",
                              (etu_id, module_id, self.user['id'], note_normale, note_rattrapage))
            except ValueError:
                messagebox.showerror("Erreur", "Les notes doivent être des nombres valides")
                conn.close()
                return
        conn.commit()
        conn.close()
        messagebox.showinfo("Succès", "Notes enregistrées")

    # --- Interface Étudiant ---

    def build_etudiant_interface(self):
        self.clear_root()
        tk.Label(self.root, text=f"Étudiant: {self.user['nom']}", font=self.font).grid(row=0, column=0)
        tk.Button(self.root, text="Voir mes notes", command=self.show_notes, font=self.font).grid(row=1, column=0)
        tk.Button(self.root, text="Déconnexion", command=self.logout, font=self.font).grid(row=2, column=0)

    def show_notes(self):
        self.clear_root()
        tk.Label(self.root, text="Mes notes", font=self.font).grid(row=0, column=0, columnspan=4)
        conn, c = get_conn_cursor()
        c.execute("""SELECT m.nom, n.note_normale, n.note_rattrapage FROM notes n
                     JOIN modules m ON n.module_id = m.id
                     WHERE n.etudiant_id=?""", (self.user['id'],))
        notes = c.fetchall()
        row = 1
        tk.Label(self.root, text="Module", font=self.font).grid(row=row, column=0)
        tk.Label(self.root, text="Note normale", font=self.font).grid(row=row, column=1)
        tk.Label(self.root, text="Note rattrapage", font=self.font).grid(row=row, column=2)
        tk.Label(self.root, text="Validé", font=self.font).grid(row=row, column=3)
        row += 1
        for mod_nom, note_normale, note_rattrapage in notes:
            valid = "Oui" if (note_normale is not None and note_normale >= 10) or (note_rattrapage is not None and note_rattrapage >= 10) else "Non"
            tk.Label(self.root, text=mod_nom, font=self.font).grid(row=row, column=0)
            tk.Label(self.root, text=str(note_normale) if note_normale is not None else '-', font=self.font).grid(row=row, column=1)
            tk.Label(self.root, text=str(note_rattrapage) if note_rattrapage is not None else '-', font=self.font).grid(row=row, column=2)
            tk.Label(self.root, text=valid, font=self.font).grid(row=row, column=3)
            row += 1
        tk.Button(self.root, text="Retour", command=self.build_etudiant_interface, font=self.font).grid(row=row, column=0, columnspan=4)
        conn.close()

    # --- Déconnexion ---

    def logout(self):
        self.user = None
        self.build_login()

if __name__ == "__main__":
    init_db()
    root = tk.Tk()
    app = GestionNotesApp(root)
    root.mainloop()
