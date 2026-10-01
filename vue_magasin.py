import customtkinter as ctk
import sqlite3
from tkinter import messagebox, simpledialog
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
from datetime import datetime

def table_pour_pole(table_name, pole):
    return table_name


def type_pour_pole(pole):
    return "3D" if pole == "3D" else "Résine"

class OngletMagasin(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global
        
        self.default_border = "#4B5563"
        self.error_border = "#EF4444"
        
        # --- MODE ADMIN ---
        self.is_admin = False 

        # Suivi pour éviter les envois multiples le même jour
        self.date_dernier_envoi = None

        # --- MISE À JOUR DE LA BASE DE DONNÉES ---
        self.mettre_a_jour_schema_bdd()

        # --- EN-TÊTE ---
        en_tete = ctk.CTkFrame(self, fg_color="transparent")
        en_tete.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(en_tete, text="🏪 Magasin & Projections", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # Boutons actions dans l'en-tête
        frame_actions = ctk.CTkFrame(en_tete, fg_color="transparent")
        frame_actions.pack(side="right")

        self.btn_admin = ctk.CTkButton(
            frame_actions, 
            text="🔒 Mode Admin", 
            width=110,
            fg_color="#4B5563", hover_color="#374151",
            command=self.basculer_admin
        )
        self.btn_admin.pack(side="left", padx=5)

        self.btn_config_mail = ctk.CTkButton(
            frame_actions, text="⚙️ Config Email", width=110, command=self.ouvrir_dialogue_config_mail
        )
        self.btn_config_mail.pack(side="left", padx=5)

        self.btn_alerte_mail = ctk.CTkButton(
            frame_actions, text="📧 Envoyer maintenant", font=ctk.CTkFont(weight="bold"), 
            fg_color="#D97706", hover_color="#B45309", command=lambda: self.envoyer_mail_automatique(manuel=True)
        )
        self.btn_alerte_mail.pack(side="left", padx=5)

        # --- ONGLETS INTERNES DU MAGASIN ---
        self.onglets = ctk.CTkTabview(self, command=self.sur_changement_onglet)
        self.onglets.pack(fill="both", expand=True)

        self.onglets.add("🔫 Scan (Stock)")
        self.onglets.add("📊 Stocks & Création")
        self.onglets.add("🔧 Pièces Maintenance")

        # ==========================================
        # 1. ONGLET : SCAN DOUCHETTE
        # ==========================================
        frame_scan = ctk.CTkFrame(self.onglets.tab("🔫 Scan (Stock)"), fg_color="transparent")
        frame_scan.pack(expand=True)

        carte_scan = ctk.CTkFrame(frame_scan, fg_color=("#E0E7FF", "#1E3A8A"), corner_radius=15)
        carte_scan.pack(ipadx=30, ipady=30)
        
        ctk.CTkLabel(carte_scan, text="Scannez ou tapez un code-barres pour gérer le stock", font=ctk.CTkFont(weight="bold", size=18)).pack(pady=(0, 10))

        # --- CHOIX ENTRÉE OU SORTIE (NOUVEAUX BOUTONS ROUGE/VERT) ---
        self.mode_scan = "Ajout"

        def set_mode_scan(mode):
            self.mode_scan = mode
            if mode == "Ajout":
                self.btn_mode_ajout.configure(fg_color="#10B981", hover_color="#059669", text_color="white")
                self.btn_mode_sortie.configure(fg_color="transparent", text_color="#EF4444", border_color="#EF4444", border_width=2)
            else:
                self.btn_mode_ajout.configure(fg_color="transparent", text_color="#10B981", border_color="#10B981", border_width=2)
                self.btn_mode_sortie.configure(fg_color="#EF4444", hover_color="#B91C1C", text_color="white")

        frame_mode = ctk.CTkFrame(carte_scan, fg_color="transparent")
        frame_mode.pack(pady=(0, 15))

        self.btn_mode_ajout = ctk.CTkButton(frame_mode, text="🟢 ENTRÉE DE STOCK (+)", font=ctk.CTkFont(weight="bold", size=16), height=40, command=lambda: set_mode_scan("Ajout"))
        self.btn_mode_ajout.pack(side="left", padx=10)

        self.btn_mode_sortie = ctk.CTkButton(frame_mode, text="🔴 SORTIE DE STOCK (-)", font=ctk.CTkFont(weight="bold", size=16), height=40, command=lambda: set_mode_scan("Sortie"))
        self.btn_mode_sortie.pack(side="left", padx=10)
        
        set_mode_scan("Ajout") # Initialisation par défaut

        frame_input_scan = ctk.CTkFrame(carte_scan, fg_color="transparent")
        frame_input_scan.pack(pady=10)

        self.entry_douchette = ctk.CTkEntry(frame_input_scan, width=350, height=45, font=ctk.CTkFont(size=18), placeholder_text="Bip ou tapez le code barre ici...")
        self.entry_douchette.pack(side="left", padx=(0, 10))
        self.entry_douchette.bind("<Return>", self.traitement_scan) 
        
        self.btn_valider_scan = ctk.CTkButton(frame_input_scan, text="Valider", height=45, font=ctk.CTkFont(weight="bold"), fg_color="#3B82F6", hover_color="#2563EB", command=self.traitement_scan)
        self.btn_valider_scan.pack(side="left")

        self.lbl_msg_scan = ctk.CTkLabel(carte_scan, text="", font=ctk.CTkFont(weight="bold", size=16))
        self.lbl_msg_scan.pack(pady=10)

        # ==========================================
        # 2. ONGLET : ÉTAT DES STOCKS & CRÉATION
        # ==========================================
        self.onglets_stocks = ctk.CTkTabview(self.onglets.tab("📊 Stocks & Création"))
        self.onglets_stocks.pack(fill="both", expand=True)
        self.onglets_stocks.add("🧱 Stocks 3D")
        self.onglets_stocks.add("💧 Stocks Résine")
        self.onglets_stocks.add("➕ Gérer Références")

        self.scroll_3d = ctk.CTkScrollableFrame(self.onglets_stocks.tab("🧱 Stocks 3D"), fg_color="transparent")
        self.scroll_3d.pack(fill="both", expand=True)
        
        self.scroll_resine = ctk.CTkScrollableFrame(self.onglets_stocks.tab("💧 Stocks Résine"), fg_color="transparent")
        self.scroll_resine.pack(fill="both", expand=True)

        # --- SOUS-ONGLET : CRÉATION DE CONSOMMABLE ---
        scroll_creation = ctk.CTkScrollableFrame(self.onglets_stocks.tab("➕ Gérer Références"), fg_color="transparent")
        scroll_creation.pack(fill="both", expand=True)

        carte_crea = ctk.CTkFrame(scroll_creation, fg_color=("gray95", "#1F2937"), corner_radius=10)
        carte_crea.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(carte_crea, text="Nouveau Consommable", font=ctk.CTkFont(weight="bold", size=18)).pack(anchor="w", padx=20, pady=(15, 10))

        grid_form = ctk.CTkFrame(carte_crea, fg_color="transparent")
        grid_form.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(grid_form, text="Pôle (Obligatoire) :").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.var_pole = ctk.StringVar(value="3D")
        radio_frame = ctk.CTkFrame(grid_form, fg_color="transparent")
        radio_frame.grid(row=0, column=1, sticky="w", pady=5, padx=15)
        ctk.CTkRadioButton(radio_frame, text="3D (FDM)", variable=self.var_pole, value="3D").pack(side="left", padx=(0, 10))
        ctk.CTkRadioButton(radio_frame, text="Résine (SLA)", variable=self.var_pole, value="Resine").pack(side="left")

        ctk.CTkLabel(grid_form, text="Nom complet (Obligatoire) :").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.entry_nom_conso = ctk.CTkEntry(grid_form, width=300, border_color=self.default_border)
        self.entry_nom_conso.grid(row=1, column=1, sticky="w", pady=5, padx=15)

        ctk.CTkLabel(grid_form, text="Matière (Obligatoire) :").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.entry_matiere = ctk.CTkEntry(grid_form, width=150, border_color=self.default_border)
        self.entry_matiere.grid(row=2, column=1, sticky="w", pady=5, padx=15)

        ctk.CTkLabel(grid_form, text="Couleur (Obligatoire) :").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.entry_couleur = ctk.CTkEntry(grid_form, width=150, border_color=self.default_border)
        self.entry_couleur.grid(row=3, column=1, sticky="w", pady=5, padx=15)
        
        ctk.CTkLabel(grid_form, text="Poids unitaire en g (Obligatoire) :").grid(row=4, column=0, sticky="w", pady=5, padx=5)
        self.entry_poids = ctk.CTkEntry(grid_form, width=150, border_color=self.default_border, placeholder_text="1000")
        self.entry_poids.grid(row=4, column=1, sticky="w", pady=5, padx=15)

        ctk.CTkLabel(grid_form, text="Stock actuel (g) :").grid(row=5, column=0, sticky="w", pady=5, padx=5)
        self.entry_qte_init = ctk.CTkEntry(grid_form, width=150, border_color=self.default_border, placeholder_text="0")
        self.entry_qte_init.grid(row=5, column=1, sticky="w", pady=5, padx=15)

        ctk.CTkLabel(grid_form, text="Stock min (g) :").grid(row=6, column=0, sticky="w", pady=5, padx=5)
        self.entry_stock_min = ctk.CTkEntry(grid_form, width=150, border_color=self.default_border, placeholder_text="500")
        self.entry_stock_min.grid(row=6, column=1, sticky="w", pady=5, padx=15)

        ctk.CTkLabel(grid_form, text="Lien achat (URL) :").grid(row=7, column=0, sticky="w", pady=5, padx=5)
        self.entry_lien_conso = ctk.CTkEntry(grid_form, width=300, border_color=self.default_border)
        self.entry_lien_conso.grid(row=7, column=1, sticky="w", pady=5, padx=15)

        ctk.CTkLabel(grid_form, text="Code-barres :").grid(row=8, column=0, sticky="w", pady=5, padx=5)
        self.entry_code_barre = ctk.CTkEntry(grid_form, width=250, border_color=self.default_border)
        self.entry_code_barre.grid(row=8, column=1, sticky="w", pady=5, padx=15)
        self.entry_code_barre.bind("<Return>", lambda event: self.creer_consommable())

        self.lbl_msg_crea = ctk.CTkLabel(scroll_creation, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_crea.pack(pady=5)
        
        ctk.CTkButton(scroll_creation, text="💾 Enregistrer au Magasin", font=ctk.CTkFont(size=16, weight="bold"), height=45, fg_color="#10B981", hover_color="#059669", command=self.creer_consommable).pack(fill="x", padx=10, pady=(0, 20))

        # --- CARTE : SUPPRESSION ---
        carte_suppr = ctk.CTkFrame(scroll_creation, fg_color=("#FEE2E2", "#451a1a"), corner_radius=10)
        carte_suppr.pack(fill="x", padx=10, pady=(20, 10))
        
        ctk.CTkLabel(carte_suppr, text="🗑️ Supprimer une référence", font=ctk.CTkFont(weight="bold", size=18), text_color="#EF4444").pack(anchor="w", padx=20, pady=(15, 5))
        grid_suppr = ctk.CTkFrame(carte_suppr, fg_color="transparent")
        grid_suppr.pack(fill="x", padx=20, pady=(0, 10))

        frame_3d = ctk.CTkFrame(grid_suppr, fg_color="transparent")
        frame_3d.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.combo_suppr_3d = ctk.CTkComboBox(frame_3d, width=250)
        self.combo_suppr_3d.pack(side="left", pady=5)
        ctk.CTkButton(frame_3d, text="Suppr. 3D", width=80, fg_color="#EF4444", hover_color="#B91C1C", command=lambda: self.supprimer_consommable("3D")).pack(side="left", padx=10)

        frame_resine = ctk.CTkFrame(grid_suppr, fg_color="transparent")
        frame_resine.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        self.combo_suppr_resine = ctk.CTkComboBox(frame_resine, width=250)
        self.combo_suppr_resine.pack(side="left", pady=5)
        ctk.CTkButton(frame_resine, text="Suppr. Résine", width=80, fg_color="#EF4444", hover_color="#B91C1C", command=lambda: self.supprimer_consommable("Resine")).pack(side="left", padx=10)

        self.lbl_msg_suppr = ctk.CTkLabel(carte_suppr, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_suppr.pack(pady=(0, 10))

        # ==========================================
        # 3. ONGLET : PIÈCES DE MAINTENANCE
        # ==========================================
        tab_maint = self.onglets.tab("🔧 Pièces Maintenance")
        self.onglets_maint = ctk.CTkTabview(tab_maint)
        self.onglets_maint.pack(fill="both", expand=True)
        self.onglets_maint.add("📋 Liste Pièces")
        self.onglets_maint.add("➕ Gérer Pièces")

        self.scroll_maintenance = ctk.CTkScrollableFrame(self.onglets_maint.tab("📋 Liste Pièces"), fg_color="transparent")
        self.scroll_maintenance.pack(fill="both", expand=True)

        # --- SOUS-ONGLET : CRÉATION DE PIÈCE ---
        scroll_crea_maint = ctk.CTkScrollableFrame(self.onglets_maint.tab("➕ Gérer Pièces"), fg_color="transparent")
        scroll_crea_maint.pack(fill="both", expand=True)

        carte_crea_m = ctk.CTkFrame(scroll_crea_maint, fg_color=("gray95", "#1F2937"), corner_radius=10)
        carte_crea_m.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(carte_crea_m, text="Nouvelle Pièce de Maintenance", font=ctk.CTkFont(weight="bold", size=18)).pack(anchor="w", padx=20, pady=(15, 10))

        grid_form_m = ctk.CTkFrame(carte_crea_m, fg_color="transparent")
        grid_form_m.pack(fill="x", padx=20, pady=(0, 20))

        ctk.CTkLabel(grid_form_m, text="Référence (Obligatoire) :").grid(row=0, column=0, sticky="w", pady=5, padx=5)
        self.entry_ref_maint = ctk.CTkEntry(grid_form_m, width=200, border_color=self.default_border, placeholder_text="ex: BUSE-04")
        self.entry_ref_maint.grid(row=0, column=1, sticky="w", pady=5, padx=15)

        ctk.CTkLabel(grid_form_m, text="Désignation (Obligatoire) :").grid(row=1, column=0, sticky="w", pady=5, padx=5)
        self.entry_des_maint = ctk.CTkEntry(grid_form_m, width=300, border_color=self.default_border)
        self.entry_des_maint.grid(row=1, column=1, sticky="w", pady=5, padx=15)

        ctk.CTkLabel(grid_form_m, text="Stock actuel :").grid(row=2, column=0, sticky="w", pady=5, padx=5)
        self.entry_qte_maint = ctk.CTkEntry(grid_form_m, width=150, border_color=self.default_border, placeholder_text="0")
        self.entry_qte_maint.grid(row=2, column=1, sticky="w", pady=5, padx=15)

        ctk.CTkLabel(grid_form_m, text="Stock min :").grid(row=3, column=0, sticky="w", pady=5, padx=5)
        self.entry_min_maint = ctk.CTkEntry(grid_form_m, width=150, border_color=self.default_border, placeholder_text="2")
        self.entry_min_maint.grid(row=3, column=1, sticky="w", pady=5, padx=15)

        ctk.CTkLabel(grid_form_m, text="Lien achat (URL) :").grid(row=4, column=0, sticky="w", pady=5, padx=5)
        self.entry_lien_maint = ctk.CTkEntry(grid_form_m, width=300, border_color=self.default_border)
        self.entry_lien_maint.grid(row=4, column=1, sticky="w", pady=5, padx=15)

        # --- NOUVEAU : Ajout du Code-barres pour les pièces de maintenance ---
        ctk.CTkLabel(grid_form_m, text="Code-barres :").grid(row=5, column=0, sticky="w", pady=5, padx=5)
        self.entry_cb_maint = ctk.CTkEntry(grid_form_m, width=250, border_color=self.default_border)
        self.entry_cb_maint.grid(row=5, column=1, sticky="w", pady=5, padx=15)

        self.lbl_msg_maint = ctk.CTkLabel(scroll_crea_maint, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_maint.pack(pady=5)

        ctk.CTkButton(scroll_crea_maint, text="💾 Enregistrer la Pièce", font=ctk.CTkFont(size=16, weight="bold"), height=45, fg_color="#10B981", hover_color="#059669", command=self.ajouter_piece_maintenance).pack(fill="x", padx=10, pady=(0, 20))

        # --- CARTE : SUPPRESSION MAINTENANCE ---
        carte_suppr_m = ctk.CTkFrame(scroll_crea_maint, fg_color=("#FEE2E2", "#451a1a"), corner_radius=10)
        carte_suppr_m.pack(fill="x", padx=10, pady=(20, 10))
        
        ctk.CTkLabel(carte_suppr_m, text="🗑️ Supprimer une pièce", font=ctk.CTkFont(weight="bold", size=18), text_color="#EF4444").pack(anchor="w", padx=20, pady=(15, 5))
        grid_suppr_m = ctk.CTkFrame(carte_suppr_m, fg_color="transparent")
        grid_suppr_m.pack(fill="x", padx=20, pady=(0, 10))

        self.combo_suppr_maint = ctk.CTkComboBox(grid_suppr_m, width=300)
        self.combo_suppr_maint.pack(side="left", pady=5, padx=(0, 10))
        ctk.CTkButton(grid_suppr_m, text="Supprimer", width=80, fg_color="#EF4444", hover_color="#B91C1C", command=self.supprimer_piece_maintenance).pack(side="left", padx=10)

        self.lbl_msg_suppr_m = ctk.CTkLabel(carte_suppr_m, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_msg_suppr_m.pack(pady=(0, 10))

        # Vérification email planifiée
        self.verifier_planification_email()

    # ==========================================
    # LOGIQUE MODE ADMIN
    # ==========================================
    def basculer_admin(self):
        if self.is_admin:
            self.is_admin = False
            self.btn_admin.configure(text="🔒 Mode Admin", fg_color="#4B5563", hover_color="#374151")
            self.charger_stocks()
            self.charger_pieces_maintenance()
        else:
            dialog = ctk.CTkInputDialog(text="Entrez le mot de passe admin :", title="Authentification")
            mdp = dialog.get_input()
            if mdp == "admin":  
                self.is_admin = True
                self.btn_admin.configure(text="🔓 Quitter Admin", fg_color="#10B981", hover_color="#059669")
                self.charger_stocks()
                self.charger_pieces_maintenance()
            elif mdp is not None:
                messagebox.showerror("Erreur", "Mot de passe incorrect.")

    # ==========================================
    # BASE DE DONNÉES & CONFIGURATION EMAIL
    # ==========================================
    def mettre_a_jour_schema_bdd(self):
        for table_name in ("consommables",):
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} (nom TEXT)")
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    colonnes = [col[1] for col in cursor.fetchall()]

                    if "quantite" not in colonnes: cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN quantite REAL DEFAULT 0")
                    if "code_barre" not in colonnes: cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN code_barre TEXT")
                    if "type_matiere" not in colonnes: cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN type_matiere TEXT")
                    if "couleur" not in colonnes: cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN couleur TEXT")
                    if "poids_unitaire" not in colonnes: cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN poids_unitaire REAL DEFAULT 1000")
                    if "stock_min" not in colonnes: cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN stock_min REAL DEFAULT 0")
                    if "lien_achat" not in colonnes: cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN lien_achat TEXT DEFAULT ''")
                    conn.commit()
            except Exception as e: print(f"Erreur MàJ {table_name}: {e}")

        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE IF NOT EXISTS pieces_maintenance (ref TEXT PRIMARY KEY, designation TEXT, quantite INTEGER DEFAULT 0)")
                cursor.execute("PRAGMA table_info(pieces_maintenance)")
                cols_maint = [col[1] for col in cursor.fetchall()]
                if "stock_min" not in cols_maint: cursor.execute("ALTER TABLE pieces_maintenance ADD COLUMN stock_min INTEGER DEFAULT 0")
                if "lien_achat" not in cols_maint: cursor.execute("ALTER TABLE pieces_maintenance ADD COLUMN lien_achat TEXT DEFAULT ''")
                if "code_barre" not in cols_maint: cursor.execute("ALTER TABLE pieces_maintenance ADD COLUMN code_barre TEXT DEFAULT ''")

                cursor.execute("CREATE TABLE IF NOT EXISTS config_email (id INTEGER PRIMARY KEY, destinataire TEXT, expediteur TEXT, mot_de_passe TEXT, serveur_smtp TEXT DEFAULT 'smtp.gmail.com', port INTEGER DEFAULT 587, heure_envoi TEXT DEFAULT '08:00')")
                conn.commit()
        except Exception as e: print(f"Erreur MàJ atelier.db: {e}")

    def charger_configuration_mail(self):
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT destinataire, expediteur, mot_de_passe, serveur_smtp, port, heure_envoi FROM config_email WHERE id = 1")
                row = cursor.fetchone()
                if row:
                    return {"destinataire": row[0], "expediteur": row[1], "mot_de_passe": row[2], "serveur_smtp": row[3], "port": row[4], "heure_envoi": row[5] or "08:00"}
        except: pass
        return None

    def verifier_planification_email(self):
        maintenant = datetime.now()
        jour_semaine = maintenant.weekday() 
        date_actuelle = maintenant.strftime("%Y-%m-%d")

        config = self.charger_configuration_mail()
        if config and config.get("destinataire") and config.get("expediteur") and config.get("mot_de_passe"):
            heure_cible = config.get("heure_envoi", "08:00")
            if jour_semaine in [0, 2] and maintenant.strftime("%H:%M") == heure_cible and self.date_dernier_envoi != date_actuelle:
                self.date_dernier_envoi = date_actuelle
                self.envoyer_mail_automatique(manuel=False)
        self.after(60000, self.verifier_planification_email)

    def envoyer_mail_automatique(self, manuel=False):
        config = self.charger_configuration_mail()
        if not config or not config.get("destinataire"):
            if manuel: messagebox.showwarning("Configuration", "Veuillez configurer vos paramètres e-mail via 'Config Email'.")
            return

        alertes = self.recuperer_alertes_stock()
        if not alertes:
            if manuel: messagebox.showinfo("Stock OK", "🎉 Aucune référence n'est en alerte.")
            return

        def executer_envoi():
            try:
                dest, exp, pwd = config["destinataire"], config["expediteur"], config["mot_de_passe"]
                host, port = config.get("serveur_smtp", "smtp.gmail.com"), int(config.get("port", 587))

                msg = MIMEMultipart("alternative")
                msg["Subject"] = f"🚨 ALERTE STOCKS ({datetime.now().strftime('%d/%m/%Y')}) : {len(alertes)} référence(s) critique(s)"
                msg["From"], msg["To"] = exp, dest

                html_lignes = ""
                for item in alertes:
                    lien_html = f'<a href="{item["lien_achat"]}">Commander</a>' if item["lien_achat"] else 'N/A'
                    unite = " g" if "3D" in item["pole"] or "Résine" in item["pole"] else " pce"
                    html_lignes += f"""
                    <tr style="border-bottom: 1px solid #ddd;">
                        <td style="padding: 10px; font-weight: bold;">{item['pole']}</td>
                        <td style="padding: 10px;">{item['nom']}</td>
                        <td style="padding: 10px; text-align: center; color: {item['couleur_hex']}; font-weight: bold;">{item['projection']:.1f}{unite}</td>
                        <td style="padding: 10px; text-align: center;">{item['stock_min']}{unite}</td>
                        <td style="padding: 10px; color: {item['couleur_hex']}; font-weight: bold;">{item['statut']}</td>
                        <td style="padding: 10px; text-align: center;">{lien_html}</td>
                    </tr>"""

                html_body = f"""<html><body style="font-family: Arial, sans-serif; color: #333;">
                    <h2 style="color: #B91C1C;">⚠️ Rapport Hebdomadaire des Stocks</h2>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
                        <tr style="background-color: #374151; color: white;">
                            <th style="padding: 10px; text-align: left;">Pôle</th><th style="padding: 10px; text-align: left;">Référence</th>
                            <th style="padding: 10px;">Projection</th><th style="padding: 10px;">Stock Min</th>
                            <th style="padding: 10px; text-align: left;">Statut</th><th style="padding: 10px;">Lien</th>
                        </tr>{html_lignes}
                    </table></body></html>"""
                msg.attach(MIMEText(html_body, "html"))
                
                with smtplib.SMTP(host, port) as server:
                    server.ehlo()
                    server.starttls()
                    server.login(exp, pwd)
                    server.sendmail(exp, [dest], msg.as_string())
                if manuel: self.after(0, lambda: messagebox.showinfo("Succès", "✅ Email envoyé !"))
            except Exception as e:
                if manuel: self.after(0, lambda: messagebox.showerror("Erreur", f"Erreur :\n{e}"))
        threading.Thread(target=executer_envoi, daemon=True).start()

    def ouvrir_dialogue_config_mail(self):
        fenetre = ctk.CTkToplevel(self)
        fenetre.title("⚙️ Paramètres Email")
        fenetre.geometry("450x520")
        fenetre.grab_set()

        ctk.CTkLabel(fenetre, text="Configuration des alertes automatiques", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 5))
        frame = ctk.CTkFrame(fenetre, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=25)

        ctk.CTkLabel(frame, text="Adresse Destinataire :", anchor="w").pack(fill="x", pady=(5, 2))
        entry_dest = ctk.CTkEntry(frame)
        entry_dest.pack(fill="x")

        ctk.CTkLabel(frame, text="Adresse Expéditeur :", anchor="w").pack(fill="x", pady=(10, 2))
        entry_exp = ctk.CTkEntry(frame)
        entry_exp.pack(fill="x")

        ctk.CTkLabel(frame, text="Mot de passe d'application :", anchor="w").pack(fill="x", pady=(10, 2))
        entry_pwd = ctk.CTkEntry(frame, show="*")
        entry_pwd.pack(fill="x")

        f_details = ctk.CTkFrame(frame, fg_color="transparent")
        f_details.pack(fill="x", pady=10)
        ctk.CTkLabel(f_details, text="Heure d'envoi :").grid(row=0, column=0, sticky="w", pady=5)
        entry_heure = ctk.CTkEntry(f_details, width=90)
        entry_heure.grid(row=0, column=1, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(f_details, text="Serveur SMTP :").grid(row=1, column=0, sticky="w", pady=5)
        entry_smtp = ctk.CTkEntry(f_details, width=160)
        entry_smtp.grid(row=1, column=1, sticky="w", padx=10, pady=5)
        ctk.CTkLabel(f_details, text="Port :").grid(row=2, column=0, sticky="w", pady=5)
        entry_port = ctk.CTkEntry(f_details, width=90)
        entry_port.grid(row=2, column=1, sticky="w", padx=10, pady=5)

        config = self.charger_configuration_mail()
        if config:
            if config.get("destinataire"): entry_dest.insert(0, config["destinataire"])
            if config.get("expediteur"): entry_exp.insert(0, config["expediteur"])
            if config.get("mot_de_passe"): entry_pwd.insert(0, config["mot_de_passe"])
            entry_heure.insert(0, config.get("heure_envoi", "08:00"))
            entry_smtp.insert(0, config.get("serveur_smtp", "smtp.gmail.com"))
            entry_port.insert(0, str(config.get("port", 587)))
        else:
            entry_heure.insert(0, "08:00")
            entry_smtp.insert(0, "smtp.gmail.com")
            entry_port.insert(0, "587")

        def sauvegarder():
            dest, exp, pwd = entry_dest.get().strip(), entry_exp.get().strip(), entry_pwd.get().strip()
            heure = entry_heure.get().strip() or "08:00"
            smtp = entry_smtp.get().strip() or "smtp.gmail.com"
            port = int(entry_port.get().strip()) if entry_port.get().strip().isdigit() else 587

            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("INSERT OR REPLACE INTO config_email (id, destinataire, expediteur, mot_de_passe, serveur_smtp, port, heure_envoi) VALUES (1, ?, ?, ?, ?, ?, ?)", (dest, exp, pwd, smtp, port, heure))
                    conn.commit()
                messagebox.showinfo("Succès", "✅ Configuration enregistrée !")
                fenetre.destroy()
            except Exception as e: messagebox.showerror("Erreur", f"Erreur : {e}")

        ctk.CTkButton(fenetre, text="💾 Enregistrer", fg_color="#10B981", hover_color="#059669", height=40, command=sauvegarder).pack(fill="x", padx=25, pady=(5, 15))

    # ==========================================
    # LOGIQUE DE L'INTERFACE
    # ==========================================
    def sur_changement_onglet(self):
        self.lbl_msg_scan.configure(text="")
        self.lbl_msg_crea.configure(text="")
        self.lbl_msg_suppr.configure(text="")
        self.lbl_msg_maint.configure(text="")
        self.lbl_msg_suppr_m.configure(text="")

        onglet_actuel = self.onglets.get()
        if onglet_actuel == "🔫 Scan (Stock)": 
            self.entry_douchette.focus()
        elif onglet_actuel == "📊 Stocks & Création": 
            self.charger_stocks()
            self.charger_liste_suppression()
        elif onglet_actuel == "🔧 Pièces Maintenance": 
            self.charger_pieces_maintenance()
            self.charger_liste_suppression_maint()

    def charger_stocks(self):
        self.afficher_liste_stocks("3D", self.scroll_3d)
        self.afficher_liste_stocks("Résine", self.scroll_resine)

    def recuperer_alertes_stock(self):
        alertes = []
        bases = [("3D", "references_generees", "commandes_clients"), ("Résine", "references_generees", "commandes_clients")]
        marge_orange_conso = 500

        # 1. Vérification des consommables
        for pole, table_references, table_commandes in bases:
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    table_consommables = table_pour_pole("consommables", pole)
                    type_production = type_pour_pole(pole)
                    cursor.execute(f"SELECT nom, quantite, stock_min, type_matiere, couleur, lien_achat FROM {table_consommables} WHERE type_production = ?", (type_production,))
                    produits = cursor.fetchall()

                    cursor.execute(f"SELECT consommable_lie, SUM(quantite * quantite_conso) FROM {table_references} WHERE type_production = ? AND statut NOT IN ('Terminée', 'Livrée') AND consommable_lie != '' GROUP BY consommable_lie", (type_production,))
                    alloc_refs = dict(cursor.fetchall())
                    
                    cursor.execute(f"SELECT consommable_lie, SUM(quantite * quantite_conso) FROM {table_commandes} WHERE type_production = ? AND statut NOT IN ('Terminée', 'Livrée') AND consommable_lie != '' GROUP BY consommable_lie", (type_production,))
                    alloc_cmds = dict(cursor.fetchall())

                for nom, qte_physique, stock_min, mat, coul, lien_achat in produits:
                    qte_physique = qte_physique if qte_physique else 0
                    stock_min = stock_min if stock_min else 0
                    qte_allouee = alloc_refs.get(nom, 0) + alloc_cmds.get(nom, 0)
                    projection = qte_physique - qte_allouee

                    detail = nom
                    if mat or coul: detail += f" ({mat or '-'} / {coul or '-'})"

                    if projection < stock_min:
                        alertes.append({
                            "pole": pole, "nom": detail, "projection": projection, "stock_min": stock_min,
                            "statut": "ROUGE (Critique)", "couleur_hex": "#EF4444", "lien_achat": lien_achat
                        })
                    elif projection <= stock_min + marge_orange_conso:
                        alertes.append({
                            "pole": pole, "nom": detail, "projection": projection, "stock_min": stock_min,
                            "statut": "ORANGE (Proche seuil)", "couleur_hex": "#F59E0B", "lien_achat": lien_achat
                        })
            except Exception as e:
                print(f"Erreur alertes conso {db_nom}: {e}")

        # 2. Vérification des pièces de maintenance
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(pieces_maintenance)")
                cols = [c[1] for c in cursor.fetchall()]
                
                if "stock_min" in cols and "lien_achat" in cols:
                    cursor.execute("SELECT ref, designation, quantite, stock_min, lien_achat FROM pieces_maintenance")
                    pieces = cursor.fetchall()
                    marge_orange_maint = 2
                    
                    for ref, des, qte, stock_min, lien_achat in pieces:
                        qte = qte if qte else 0
                        stock_min = stock_min if stock_min else 0
                        
                        if qte < stock_min:
                            alertes.append({
                                "pole": "🔧 Maintenance", "nom": f"[{ref}] {des}", "projection": qte, "stock_min": stock_min,
                                "statut": "ROUGE (Rupture)", "couleur_hex": "#EF4444", "lien_achat": lien_achat
                            })
                        elif qte <= stock_min + marge_orange_maint:
                            alertes.append({
                                "pole": "🔧 Maintenance", "nom": f"[{ref}] {des}", "projection": qte, "stock_min": stock_min,
                                "statut": "ORANGE (Proche seuil)", "couleur_hex": "#F59E0B", "lien_achat": lien_achat
                            })
        except Exception as e:
            print(f"Erreur alertes maintenance: {e}")

        return alertes

    # ==========================================
    # LOGIQUE SUPPRESSION
    # ==========================================
    def charger_liste_suppression(self):
        noms_3d, noms_resine = [], []
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nom FROM consommables WHERE type_production = '3D' ORDER BY nom")
                noms_3d = [row[0] for row in cursor.fetchall()]
        except: pass
        self.combo_suppr_3d.configure(values=noms_3d if noms_3d else ["Aucun consommable"])
        self.combo_suppr_3d.set(noms_3d[0] if noms_3d else "Aucun consommable")

        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT nom FROM consommables WHERE type_production = 'Résine' ORDER BY nom")
                noms_resine = [row[0] for row in cursor.fetchall()]
        except: pass
        self.combo_suppr_resine.configure(values=noms_resine if noms_resine else ["Aucun consommable"])
        self.combo_suppr_resine.set(noms_resine[0] if noms_resine else "Aucun consommable")

    def supprimer_consommable(self, pole):
        nom = self.combo_suppr_3d.get() if pole == "3D" else self.combo_suppr_resine.get()
        table_cible = table_pour_pole("consommables", pole)
        if not nom or nom == "Aucun consommable": return
            
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer '{nom}' ?\nAction irréversible."):
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"DELETE FROM {table_cible} WHERE type_production = ? AND nom = ?", (type_pour_pole(pole), nom))
                    conn.commit()
                self.lbl_msg_suppr.configure(text=f"✅ '{nom}' a été supprimé.", text_color="#10B981")
                self.after(4000, lambda: self.lbl_msg_suppr.configure(text=""))
                self.charger_liste_suppression()
                self.charger_stocks()
                if self.fonction_rafraichir_global: self.fonction_rafraichir_global()
            except Exception as e: self.lbl_msg_suppr.configure(text=f"❌ Erreur : {e}", text_color=self.error_border)

    def charger_liste_suppression_maint(self):
        refs = []
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ref, designation FROM pieces_maintenance ORDER BY ref")
                refs = [f"[{row[0]}] {row[1]}" for row in cursor.fetchall()]
        except: pass
        
        if refs:
            self.combo_suppr_maint.configure(values=refs)
            self.combo_suppr_maint.set(refs[0])
        else:
            self.combo_suppr_maint.configure(values=["Aucune pièce"])
            self.combo_suppr_maint.set("Aucune pièce")

    def supprimer_piece_maintenance(self):
        selection = self.combo_suppr_maint.get()
        if not selection or selection == "Aucune pièce": return
        
        ref = selection.split("]")[0].replace("[", "")
        
        if messagebox.askyesno("Confirmation", f"Êtes-vous sûr de vouloir supprimer la pièce '{ref}' ?\nAction irréversible."):
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM pieces_maintenance WHERE ref = ?", (ref,))
                    conn.commit()
                self.lbl_msg_suppr_m.configure(text=f"✅ Pièce '{ref}' supprimée.", text_color="#10B981")
                self.after(4000, lambda: self.lbl_msg_suppr_m.configure(text=""))
                self.charger_liste_suppression_maint()
                self.charger_pieces_maintenance()
                if self.fonction_rafraichir_global: self.fonction_rafraichir_global()
            except Exception as e:
                self.lbl_msg_suppr_m.configure(text=f"❌ Erreur : {e}", text_color=self.error_border)

    # ==========================================
    # 1. LOGIQUE SCAN DOUCHETTE
    # ==========================================
    def traitement_scan(self, event=None):
        code_scanne = self.entry_douchette.get().strip()
        if not code_scanne: return
        produit_trouve = False
        mode = getattr(self, 'mode_scan', 'Ajout') # "Ajout" ou "Sortie"
        
        # 1. Recherche dans les consommables
        for pole in ("3D", "Résine"):
            if produit_trouve: break
            try:
                table_consommables = table_pour_pole("consommables", pole)
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    type_production = type_pour_pole(pole)
                    cursor.execute(f"SELECT nom, quantite, poids_unitaire FROM {table_consommables} WHERE type_production = ? AND code_barre = ?", (type_production, code_scanne))
                    result = cursor.fetchone()
                    if result:
                        nom_prod, qte_actuelle, poids_unitaire = result
                        ajout = poids_unitaire if poids_unitaire is not None else 1000.0
                        qte_act = qte_actuelle if qte_actuelle else 0

                        if mode == "Ajout":
                            nouvelle_qte = qte_act + ajout
                            signe = "+"
                            c_msg = "#10B981" # Vert
                        else:
                            nouvelle_qte = max(0, qte_act - ajout)
                            signe = "-"
                            c_msg = "#EF4444" # Rouge pour une sortie

                        cursor.execute(f"UPDATE {table_consommables} SET quantite = ? WHERE type_production = ? AND code_barre = ?", (nouvelle_qte, type_production, code_scanne))
                        conn.commit()
                        produit_trouve = True
                        self.lbl_msg_scan.configure(text=f"✅ {signe}{ajout}g de stock pour '{nom_prod}' ({pole})", text_color=c_msg)
            except: pass

        # 2. Recherche dans les pièces de maintenance (Nouveauté)
        if not produit_trouve:
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT ref, designation, quantite FROM pieces_maintenance WHERE code_barre = ?", (code_scanne,))
                    result = cursor.fetchone()
                    if result:
                        ref, des, qte_actuelle = result
                        ajout = 1 # Pour une pièce, on enlève ou on rajoute toujours par 1
                        qte_act = qte_actuelle if qte_actuelle else 0

                        if mode == "Ajout":
                            nouvelle_qte = qte_act + ajout
                            signe = "+"
                            c_msg = "#10B981" # Vert
                        else:
                            nouvelle_qte = max(0, qte_act - ajout)
                            signe = "-"
                            c_msg = "#EF4444" # Rouge

                        cursor.execute("UPDATE pieces_maintenance SET quantite = ? WHERE ref = ?", (nouvelle_qte, ref))
                        conn.commit()
                        produit_trouve = True
                        self.lbl_msg_scan.configure(text=f"✅ {signe}{ajout} unité pour la pièce '{des}'", text_color=c_msg)
            except Exception as e: print(f"Erreur scan maintenance: {e}")

        if not produit_trouve: self.lbl_msg_scan.configure(text=f"❌ Code '{code_scanne}' inconnu.", text_color=self.error_border)
        self.entry_douchette.delete(0, 'end')
        self.entry_douchette.focus()
        self.after(4000, lambda: self.lbl_msg_scan.configure(text=""))
        if self.fonction_rafraichir_global: self.fonction_rafraichir_global()

    # ==========================================
    # 2. LOGIQUE D'AFFICHAGE ET D'ÉDITION STOCKS
    # ==========================================
    def afficher_liste_stocks(self, db_nom, scroll_frame):
        for widget in scroll_frame.winfo_children(): widget.destroy()

        try:
            table_consommables = table_pour_pole("consommables", db_nom)
            table_references = table_pour_pole("references_generees", db_nom)
            table_commandes = table_pour_pole("commandes_clients", db_nom)
            type_production = type_pour_pole(db_nom)
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT nom, quantite, type_matiere, couleur, code_barre, stock_min FROM {table_consommables} WHERE type_production = ? ORDER BY nom", (type_production,))
                produits = cursor.fetchall()

                cursor.execute(f"SELECT consommable_lie, SUM(quantite * quantite_conso) FROM {table_references} WHERE type_production = ? AND statut NOT IN ('Terminée', 'Livrée') AND consommable_lie != '' GROUP BY consommable_lie", (type_production,))
                alloc_refs = dict(cursor.fetchall())
                cursor.execute(f"SELECT consommable_lie, SUM(quantite * quantite_conso) FROM {table_commandes} WHERE type_production = ? AND statut NOT IN ('Terminée', 'Livrée') AND consommable_lie != '' GROUP BY consommable_lie", (type_production,))
                alloc_cmds = dict(cursor.fetchall())

            if not produits:
                ctk.CTkLabel(scroll_frame, text="📭 Aucun consommable.", font=ctk.CTkFont(slant="italic")).pack(pady=30)
                return

            en_tete = ctk.CTkFrame(scroll_frame, fg_color="#374151")
            en_tete.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(en_tete, text="Référence", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
            
            frame_droite = ctk.CTkFrame(en_tete, fg_color="transparent")
            frame_droite.pack(side="right", padx=10)
            ctk.CTkLabel(frame_droite, text="Physique", width=70, font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(frame_droite, text="Alloué", width=70, font=ctk.CTkFont(weight="bold"), text_color="orange").pack(side="left", padx=5)
            ctk.CTkLabel(frame_droite, text="Projection", width=90, font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(frame_droite, text="Min", width=60, font=ctk.CTkFont(weight="bold")).pack(side="left")

            for nom, qte_physique, mat, coul, code, stock_min in produits:
                qte_physique = qte_physique if qte_physique else 0
                stock_min = stock_min if stock_min else 0
                qte_allouee = alloc_refs.get(nom, 0) + alloc_cmds.get(nom, 0)
                projection = qte_physique - qte_allouee

                if projection < stock_min: c_proj, couleur_fond = "#EF4444", ("#fee2e2" if ctk.get_appearance_mode() == "Light" else "#451a1a")
                elif projection <= stock_min + 500: c_proj, couleur_fond = "#F59E0B", ("#fef08a" if ctk.get_appearance_mode() == "Light" else "#4d3800")
                else: c_proj, couleur_fond = "#10B981", ("gray95" if ctk.get_appearance_mode() == "Light" else "#1F2937")
                
                ligne = ctk.CTkFrame(scroll_frame, fg_color=couleur_fond)
                ligne.pack(fill="x", pady=2)

                desc = f"{nom}"
                if mat or coul: desc += f" ({mat or '-'} / {coul or '-'})"
                ctk.CTkLabel(ligne, text=desc, font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10, pady=8)
                
                f_chiffres = ctk.CTkFrame(ligne, fg_color="transparent")
                f_chiffres.pack(side="right", padx=10)
                
                if self.is_admin:
                    entry_phys = ctk.CTkEntry(f_chiffres, width=60, height=24, font=ctk.CTkFont(size=13))
                    entry_phys.insert(0, str(round(qte_physique, 1)))
                    entry_phys.pack(side="left", padx=(0, 10))
                    entry_phys.bind("<Return>", lambda event, pole=db_nom, n=nom, e=entry_phys: self.maj_stock_physique(event, pole, n, e))
                else:
                    ctk.CTkLabel(f_chiffres, text=f"{qte_physique:.1f}", width=60, font=ctk.CTkFont(size=14)).pack(side="left", padx=(0, 10))

                ctk.CTkLabel(f_chiffres, text=f"{qte_allouee:.1f}", width=70, font=ctk.CTkFont(size=14), text_color="orange").pack(side="left")
                ctk.CTkLabel(f_chiffres, text=f"{projection:.1f}", width=90, font=ctk.CTkFont(size=15, weight="bold"), text_color=c_proj).pack(side="left")

                if self.is_admin:
                    entry_min = ctk.CTkEntry(f_chiffres, width=50, height=24, font=ctk.CTkFont(size=12))
                    entry_min.insert(0, str(int(stock_min) if stock_min.is_integer() else stock_min))
                    entry_min.pack(side="left", padx=(10, 0))
                    entry_min.bind("<Return>", lambda event, pole=db_nom, n=nom, e=entry_min: self.maj_stock_min(event, pole, n, e))
                else:
                    ctk.CTkLabel(f_chiffres, text=f"{stock_min:.0f}", width=50).pack(side="left", padx=(10, 0))

        except Exception as e: ctk.CTkLabel(scroll_frame, text=f"⚠️ Erreur BDD : {e}").pack(pady=20)

    def maj_stock_physique(self, event, db_nom, nom_produit, entry_widget):
        if not entry_widget.winfo_exists(): return
        valeur = entry_widget.get().strip()
        if not valeur: valeur = "0"
        try:
            nouvelle_qte = float(valeur.replace(',', '.'))
            table_consommables = table_pour_pole("consommables", db_nom)
            type_production = type_pour_pole(db_nom)
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE {table_consommables} SET quantite = ? WHERE type_production = ? AND nom = ?", (nouvelle_qte, type_production, nom_produit))
                conn.commit()
            self.charger_stocks()
            if event and event.keysym == "Return": self.focus()
            if self.fonction_rafraichir_global: self.fonction_rafraichir_global()
        except ValueError: entry_widget.configure(border_color=self.error_border)

    def maj_stock_min(self, event, db_nom, nom_produit, entry_widget):
        if not entry_widget.winfo_exists(): return
        valeur = entry_widget.get().strip()
        if not valeur: valeur = "0"
        try:
            nouveau_min = float(valeur.replace(',', '.'))
            table_consommables = table_pour_pole("consommables", db_nom)
            type_production = type_pour_pole(db_nom)
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute(f"UPDATE {table_consommables} SET stock_min = ? WHERE type_production = ? AND nom = ?", (nouveau_min, type_production, nom_produit))
                conn.commit()
            self.charger_stocks()
            if event and event.keysym == "Return": self.focus()
        except ValueError: entry_widget.configure(border_color=self.error_border)

    # ==========================================
    # LOGIQUE CRÉATION CONSOMMABLE
    # ==========================================
    def creer_consommable(self):
        table_consommables = table_pour_pole("consommables", self.var_pole.get())
        type_production = type_pour_pole(self.var_pole.get())
        nom, mat, coul = self.entry_nom_conso.get().strip(), self.entry_matiere.get().strip(), self.entry_couleur.get().strip()
        code, lien = self.entry_code_barre.get().strip(), self.entry_lien_conso.get().strip()
        p_txt = self.entry_poids.get().strip()

        if not nom or not mat or not coul or not p_txt:
            self.lbl_msg_crea.configure(text="⚠️ Les champs (Nom, Matière, Couleur, Poids) sont obligatoires.", text_color=self.error_border)
            return

        poids = float(p_txt.replace(',', '.')) if p_txt.replace('.', '', 1).isdigit() else 1000.0

        q_txt = self.entry_qte_init.get().strip()
        qte_init = float(q_txt.replace(',', '.')) if q_txt.replace('.', '', 1).isdigit() else 0.0

        m_txt = self.entry_stock_min.get().strip()
        stock_min = float(m_txt.replace(',', '.')) if m_txt.replace('.', '', 1).isdigit() else 0.0

        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute(f"""
                    INSERT INTO {table_consommables} (type_production, nom, quantite, type_matiere, couleur, code_barre, poids_unitaire, stock_min, lien_achat)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (type_production, nom, qte_init, mat, coul, code, poids, stock_min, lien))
                conn.commit()
            
            self.lbl_msg_crea.configure(text=f"✅ '{nom}' enregistré !", text_color="#10B981")
            for entry in [self.entry_nom_conso, self.entry_matiere, self.entry_couleur, self.entry_code_barre, self.entry_poids, self.entry_qte_init, self.entry_stock_min, self.entry_lien_conso]:
                entry.delete(0, 'end')
            
            self.entry_nom_conso.focus()
            self.after(4000, lambda: self.lbl_msg_crea.configure(text=""))
            self.charger_liste_suppression()
            self.charger_stocks()
            if self.fonction_rafraichir_global: self.fonction_rafraichir_global()

        except sqlite3.IntegrityError: self.lbl_msg_crea.configure(text="⚠️ Référence ou Code-barres déjà utilisé.", text_color=self.error_border)
        except Exception as e: self.lbl_msg_crea.configure(text=f"❌ Erreur: {e}", text_color=self.error_border)

    # ==========================================
    # LOGIQUE MAINTENANCE AVEC MODE ADMIN
    # ==========================================
    def ajouter_piece_maintenance(self):
        ref, des = self.entry_ref_maint.get().strip(), self.entry_des_maint.get().strip()
        lien, m_txt = self.entry_lien_maint.get().strip(), self.entry_min_maint.get().strip()
        q_txt = self.entry_qte_maint.get().strip()
        cb = self.entry_cb_maint.get().strip()
        
        if not ref or not des:
            self.lbl_msg_maint.configure(text="⚠️ Les champs (Référence, Désignation) sont obligatoires.", text_color=self.error_border)
            self.after(3000, lambda: self.lbl_msg_maint.configure(text=""))
            return
            
        stock_min = int(m_txt) if m_txt.isdigit() else 0
        qte_actuelle = int(q_txt) if q_txt.isdigit() else 0
            
        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO pieces_maintenance (ref, designation, quantite, stock_min, lien_achat, code_barre) VALUES (?, ?, ?, ?, ?, ?)", (ref, des, qte_actuelle, stock_min, lien, cb))
                conn.commit()
            
            self.lbl_msg_maint.configure(text=f"✅ Pièce '{ref}' enregistrée !", text_color="#10B981")
            for entry in [self.entry_ref_maint, self.entry_des_maint, self.entry_min_maint, self.entry_qte_maint, self.entry_lien_maint, self.entry_cb_maint]:
                entry.delete(0, 'end')
            
            self.charger_pieces_maintenance()
            self.charger_liste_suppression_maint()
            self.after(3000, lambda: self.lbl_msg_maint.configure(text=""))
        except sqlite3.IntegrityError:
            self.lbl_msg_maint.configure(text="⚠️ Cette référence existe déjà.", text_color=self.error_border)
            self.after(3000, lambda: self.lbl_msg_maint.configure(text=""))
        except Exception as e:
            self.lbl_msg_maint.configure(text=f"❌ Erreur: {e}", text_color=self.error_border)
            self.after(3000, lambda: self.lbl_msg_maint.configure(text=""))

    def charger_pieces_maintenance(self):
        for widget in self.scroll_maintenance.winfo_children(): widget.destroy()

        try:
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ref, designation, quantite, stock_min FROM pieces_maintenance ORDER BY ref")
                pieces = cursor.fetchall()

            if not pieces: 
                ctk.CTkLabel(self.scroll_maintenance, text="📭 Aucune pièce enregistrée.", font=ctk.CTkFont(slant="italic")).pack(pady=30)
                return

            en_tete = ctk.CTkFrame(self.scroll_maintenance, fg_color="#374151")
            en_tete.pack(fill="x", pady=(0, 5))
            ctk.CTkLabel(en_tete, text="Référence - Désignation", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=5)
            
            frame_droite = ctk.CTkFrame(en_tete, fg_color="transparent")
            frame_droite.pack(side="right", padx=10)
            ctk.CTkLabel(frame_droite, text="Actuel", font=ctk.CTkFont(weight="bold"), width=60).pack(side="left")
            ctk.CTkLabel(frame_droite, text="Min", font=ctk.CTkFont(weight="bold"), width=60).pack(side="left", padx=10)

            for ref, des, qte, stock_min in pieces:
                qte = qte if qte else 0
                stock_min = stock_min if stock_min else 0
                
                if qte < stock_min: c_txt, fond = "#EF4444", ("#fee2e2" if ctk.get_appearance_mode() == "Light" else "#451a1a")
                elif qte <= stock_min + 2: c_txt, fond = "#F59E0B", ("#fef08a" if ctk.get_appearance_mode() == "Light" else "#4d3800")
                else: c_txt, fond = "#10B981", ("gray95" if ctk.get_appearance_mode() == "Light" else "#1F2937")

                ligne = ctk.CTkFrame(self.scroll_maintenance, fg_color=fond)
                ligne.pack(fill="x", pady=2)

                ctk.CTkLabel(ligne, text=f"[{ref}] {des}", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=10, pady=8)

                f_actions = ctk.CTkFrame(ligne, fg_color="transparent")
                f_actions.pack(side="right", padx=10)

                # Pas de boutons + ou -
                if self.is_admin:
                    entry_qte = ctk.CTkEntry(f_actions, width=50, height=24, font=ctk.CTkFont(size=14, weight="bold"))
                    entry_qte.insert(0, str(qte))
                    entry_qte.pack(side="left", padx=5)
                    entry_qte.bind("<Return>", lambda event, r=ref, e=entry_qte: self.maj_stock_physique_piece(event, r, e))
                else:
                    ctk.CTkLabel(f_actions, text=str(qte), width=50, font=ctk.CTkFont(size=16, weight="bold"), text_color=c_txt).pack(side="left", padx=5)

                if self.is_admin:
                    entry_min = ctk.CTkEntry(f_actions, width=50, height=24, font=ctk.CTkFont(size=12))
                    entry_min.insert(0, str(stock_min))
                    entry_min.pack(side="left", padx=(15, 5))
                    entry_min.bind("<Return>", lambda event, r=ref, e=entry_min: self.maj_stock_min_piece(event, r, e))
                else:
                    ctk.CTkLabel(f_actions, text=str(stock_min), width=50).pack(side="left", padx=(15, 5))

        except Exception as e: print(f"Erreur Maintenance : {e}")

    def maj_stock_physique_piece(self, event, ref_piece, entry_widget):
        if not entry_widget.winfo_exists(): return
        valeur = entry_widget.get().strip()
        try:
            nouvelle_qte = int(valeur) if valeur else 0
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE pieces_maintenance SET quantite = ? WHERE ref = ?", (nouvelle_qte, ref_piece))
                conn.commit()
            self.charger_pieces_maintenance()
            if event and event.keysym == "Return": self.focus()
            if self.fonction_rafraichir_global: self.fonction_rafraichir_global()
        except ValueError: entry_widget.configure(border_color=self.error_border)

    def maj_stock_min_piece(self, event, ref_piece, entry_widget):
        if not entry_widget.winfo_exists(): return
        valeur = entry_widget.get().strip()
        try:
            nouveau_min = int(valeur) if valeur else 0
            with sqlite3.connect("atelier.db") as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE pieces_maintenance SET stock_min = ? WHERE ref = ?", (nouveau_min, ref_piece))
                conn.commit()
            self.charger_pieces_maintenance()
            if event and event.keysym == "Return": self.focus()
        except ValueError: entry_widget.configure(border_color=self.error_border)