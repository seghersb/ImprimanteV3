import customtkinter as ctk
import sqlite3
from datetime import datetime

class OngletAjoutProduction(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global

        # --- EN-TÊTE ---
        en_tete = ctk.CTkFrame(self, fg_color="transparent")
        en_tete.pack(fill="x", pady=(0, 15))
        ctk.CTkLabel(en_tete, text="⚙️ Ajout de Production", font=ctk.CTkFont(size=26, weight="bold")).pack(side="left")

        # --- CONTENEUR DÉROULANT ---
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True, padx=0, pady=0)

        # Variables de contrôle
        self.var_pole = ctk.StringVar(value="3D")
        self.var_source = ctk.StringVar(value="Interne")
        self.var_priorite = ctk.StringVar(value="Dans le flux")
        self.default_border = "#4B5563"
        self.error_border = "#EF4444"

        # ==========================================
        # ÉTAPE 1 : CHOIX DE LA RÉFÉRENCE
        # ==========================================
        self.frame_etape1 = self.creer_carte("1️⃣ ÉTAPE 1 : Choisir la pièce à planifier")
        self.frame_etape1.master.pack(fill="x", pady=10, padx=5)

        radio_source = ctk.CTkFrame(self.frame_etape1, fg_color="transparent")
        radio_source.pack(anchor="w", pady=(0, 10))
        ctk.CTkRadioButton(radio_source, text="📁 Références Internes", variable=self.var_source, value="Interne", command=self.sur_changement_source, text_color="#3B82F6", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 25))
        ctk.CTkRadioButton(radio_source, text="🛒 Commandes Clients", variable=self.var_source, value="Client", command=self.sur_changement_source, text_color="#10B981", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

        ctk.CTkLabel(self.frame_etape1, text="Sélectionnez l'élément :", text_color="gray60").pack(anchor="w", pady=(5, 2))
        self.combo_refs = ctk.CTkComboBox(self.frame_etape1, width=400, border_color=self.default_border, command=self.sur_selection_reference)
        self.combo_refs.pack(anchor="w")

        # ==========================================
        # ÉTAPE 2 : QUANTITÉ
        # ==========================================
        self.frame_etape2 = self.creer_carte("2️⃣ ÉTAPE 2 : Quantité à produire")
        self.frame_etape2.master.pack(fill="x", pady=10, padx=5)

        frame_qte = ctk.CTkFrame(self.frame_etape2, fg_color="transparent")
        frame_qte.pack(anchor="w", pady=5)
        
        ctk.CTkLabel(frame_qte, text="Quantité :", text_color="gray60").pack(side="left", padx=5)
        self.entry_qte = ctk.CTkEntry(frame_qte, width=100, border_color=self.default_border)
        self.entry_qte.insert(0, "1")
        self.entry_qte.pack(side="left", padx=10)

        # ==========================================
        # ÉTAPE 3 : PARAMÈTRES DE PRODUCTION (Slicer)
        # ==========================================
        self.frame_etape3 = self.creer_carte("3️⃣ ÉTAPE 3 : Paramètres de Production (Slicer)")
        self.frame_etape3.master.pack(fill="x", pady=10, padx=5)

        grid_params = ctk.CTkFrame(self.frame_etape3, fg_color="transparent")
        grid_params.pack(fill="x", pady=5)

        # Ligne 1 : Choix du flux et Temps
        ctk.CTkLabel(grid_params, text="Flux de prod. :", text_color="gray60").grid(row=0, column=0, sticky="w", padx=5, pady=10)
        
        radio_frame = ctk.CTkFrame(grid_params, fg_color="transparent")
        radio_frame.grid(row=0, column=1, sticky="w", padx=10, pady=10)
        ctk.CTkRadioButton(radio_frame, text="🧱 Pôle 3D (FDM)", variable=self.var_pole, value="3D", command=self.charger_references, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(0, 15))
        ctk.CTkRadioButton(radio_frame, text="💧 Pôle Résine (SLA)", variable=self.var_pole, value="Resine", command=self.charger_references, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10)

        ctk.CTkLabel(grid_params, text="Temps d'impression (min) :", text_color="gray60").grid(row=0, column=2, sticky="w", padx=(25, 5), pady=10)
        self.entry_temps = ctk.CTkEntry(grid_params, width=100, border_color=self.default_border)
        self.entry_temps.insert(0, "0")
        self.entry_temps.grid(row=0, column=3, sticky="w", padx=10, pady=10)

        # Ligne 2 : Poids et Matière liée au Magasin
        ctk.CTkLabel(grid_params, text="Poids unitaire (g) :", text_color="gray60").grid(row=1, column=0, sticky="w", padx=5, pady=10)
        self.entry_poids = ctk.CTkEntry(grid_params, width=100, border_color=self.default_border)
        self.entry_poids.insert(0, "0.0")
        self.entry_poids.grid(row=1, column=1, sticky="w", padx=10, pady=10)

        ctk.CTkLabel(grid_params, text="Matière (Magasin) :", text_color="gray60").grid(row=1, column=2, sticky="w", padx=(25, 5), pady=10)
        self.combo_conso = ctk.CTkComboBox(grid_params, width=220, border_color=self.default_border)
        self.combo_conso.grid(row=1, column=3, sticky="w", padx=10, pady=10)

        # ==========================================
        # ÉTAPE 4 : ORDRE DE PRIORITÉ
        # ==========================================
        self.frame_etape4 = self.creer_carte("4️⃣ ÉTAPE 4 : Ordre de priorité")
        self.frame_etape4.master.pack(fill="x", pady=10, padx=5)

        grid_priorite = ctk.CTkFrame(self.frame_etape4, fg_color="transparent")
        grid_priorite.pack(fill="x", pady=5)

        self.combo_priorite = ctk.CTkOptionMenu(grid_priorite, values=["Dans le flux", "Urgence", "Avant échéance"], variable=self.var_priorite, command=self.sur_changement_priorite, fg_color="#374151")
        self.combo_priorite.grid(row=0, column=0, sticky="w")

        self.frame_echeance = ctk.CTkFrame(grid_priorite, fg_color="transparent")
        ctk.CTkLabel(self.frame_echeance, text="Date (JJ/MM) :").pack(side="left", padx=(15, 5))
        self.entry_echeance = ctk.CTkEntry(self.frame_echeance, width=100, placeholder_text="ex: 15/10", border_color=self.default_border)
        self.entry_echeance.pack(side="left")

        # ==========================================
        # VALIDATION FINALE
        # ==========================================
        self.frame_resultat = ctk.CTkFrame(self.scroll_frame, fg_color="transparent")
        self.frame_resultat.pack(pady=10)

        self.lbl_message = ctk.CTkLabel(self.frame_resultat, text="", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_message.pack()

        ctk.CTkButton(self.scroll_frame, text="🚀 Envoyer au Planning", font=ctk.CTkFont(size=16, weight="bold"), height=50, fg_color="#1D4ED8", hover_color="#1E3A8A", command=self.envoyer_production).pack(fill="x", padx=5, pady=(0, 20))

        # Initialisation
        self.charger_references()
        self.sur_changement_priorite(self.var_priorite.get())

    # ==========================================
    # MÉTHODES D'INTERFACE & CHARGEMENT
    # ==========================================
    def creer_carte(self, titre):
        carte = ctk.CTkFrame(self.scroll_frame, fg_color=("gray95", "#1F2937"), corner_radius=10)
        ctk.CTkLabel(carte, text=titre, font=ctk.CTkFont(weight="bold", size=15)).pack(anchor="w", padx=15, pady=(15, 5))
        contenu = ctk.CTkFrame(carte, fg_color="transparent")
        contenu.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        return contenu

    def sur_changement_priorite(self, choix):
        if choix == "Avant échéance":
            self.frame_echeance.grid(row=0, column=1, sticky="w")
        else:
            self.frame_echeance.grid_forget()

    def get_db_name(self):
        return "atelier.db"

    def get_table_name(self, table_name, pole=None):
        return table_name

    def get_type_production(self, pole=None):
        pole = pole or self.var_pole.get()
        return "3D" if pole == "3D" else "Résine"

    def sur_changement_source(self):
        self.charger_references()

    def charger_consommables(self):
        """Récupère les matières exactes disponibles dans le magasin."""
        db_cible = self.get_db_name()
        table_consommables = self.get_table_name("consommables")
        try:
            with sqlite3.connect(db_cible, timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT nom FROM {table_consommables} WHERE type_production = ? ORDER BY nom", (self.get_type_production(),))
                produits = cursor.fetchall()
                valeurs = [p[0] for p in produits] if produits else ["--- Aucun consommable ---"]
                self.combo_conso.configure(values=valeurs)
                self.combo_conso.set(valeurs[0])
        except:
            self.combo_conso.configure(values=["--- Aucun consommable ---"])
            self.combo_conso.set("--- Aucun consommable ---")

    def charger_references(self):
        self.charger_consommables()
        source = self.var_source.get()
        valeurs_uniques = set()
        
        def recuperer_refs(table_name, pole):
            try:
                with sqlite3.connect("atelier.db", timeout=30.0) as conn:
                    cursor = conn.cursor()
                    if source == "Interne":
                        cursor.execute(f"SELECT reference_complete FROM {table_name} WHERE type_production = ? ORDER BY id DESC", (self.get_type_production(pole),))
                        return [r[0] for r in cursor.fetchall()]
                    elif source == "Client":
                        cursor.execute(f"SELECT reference_piece, quantite FROM {table_name} WHERE type_production = ? AND statut = 'Créée' ORDER BY id DESC", (self.get_type_production(pole),))
                        return [f"{nom} (Qté: {qte})" for nom, qte in cursor.fetchall()]
            except sqlite3.OperationalError:
                return [] 

        valeurs_uniques.update(recuperer_refs(self.get_table_name("references_generees", "3D") if source == "Interne" else self.get_table_name("commandes_clients", "3D"), "3D"))
        valeurs_uniques.update(recuperer_refs(self.get_table_name("references_generees", "Resine") if source == "Interne" else self.get_table_name("commandes_clients", "Resine"), "Resine"))
        
        valeurs = sorted(list(valeurs_uniques))
        
        if not valeurs:
            valeurs = ["--- Aucune donnée disponible ---"]
            
        self.combo_refs.configure(values=valeurs)
        self.combo_refs.set(valeurs[0])
        self.sur_selection_reference(valeurs[0])

    def sur_selection_reference(self, choix):
        if not choix or choix.startswith("---"):
            return
            
        nom_pur = choix.split(" (Qté:")[0].strip()
        source = self.var_source.get()
        row = None

        for pole in ("3D", "Resine"):
            type_production = self.get_type_production(pole)
            try:
                with sqlite3.connect("atelier.db") as conn:
                    cursor = conn.cursor()
                    if source == "Interne":
                        table_name = self.get_table_name("references_generees", pole)
                        cursor.execute(f"SELECT quantite, temps_unitaire, quantite_conso, consommable_lie FROM {table_name} WHERE type_production = ? AND reference_complete = ?", (type_production, nom_pur))
                    else:
                        table_name = self.get_table_name("commandes_clients", pole)
                        cursor.execute(f"SELECT quantite, temps_unitaire, quantite_conso, consommable_lie FROM {table_name} WHERE type_production = ? AND reference_piece = ?", (type_production, nom_pur))
                    
                    resultat = cursor.fetchone()
                    if resultat:
                        row = resultat
                        break 
            except sqlite3.OperationalError:
                pass 

        if row:
            qte, temps, poids, conso = row
            
            self.entry_qte.delete(0, 'end')
            self.entry_qte.insert(0, str(qte) if qte else "1")
            
            self.entry_temps.delete(0, 'end')
            self.entry_temps.insert(0, str(temps) if temps else "0")
            
            self.entry_poids.delete(0, 'end')
            self.entry_poids.insert(0, str(poids) if poids else "0.0")
            
            if conso and conso in self.combo_conso.cget("values"):
                self.combo_conso.set(conso)

    # ==========================================
    # VALIDATION ET ENVOI AVEC RESET DATE_LANCEMENT
    # ==========================================
    def envoyer_production(self):
        selection = self.combo_refs.get()
        if not selection or selection.startswith("---"):
            self.lbl_message.configure(text="⚠️ Veuillez sélectionner un élément valide.", text_color=self.error_border)
            return
            
        qte_texte = self.entry_qte.get().strip()
        qte = int(qte_texte) if qte_texte.isdigit() else 1
        temps_texte = self.entry_temps.get().strip()
        temps = int(temps_texte) if temps_texte.isdigit() else 0
        poids_texte = self.entry_poids.get().replace(',', '.').strip()
        poids = float(poids_texte) if poids_texte.replace('.', '', 1).isdigit() else 0.0
        
        conso = self.combo_conso.get()
        if conso.startswith("---"): conso = ""

        statut_priorite = self.var_priorite.get()
        echeance = self.entry_echeance.get().strip() if statut_priorite == "Avant échéance" else ""

        flux_nom = "3D" if self.var_pole.get() == "3D" else "Résine"
        source = self.var_source.get()
        nom_pur = selection.split(" (Qté:")[0].strip()
        table_base = "references_generees" if source == "Interne" else "commandes_clients"
        table_dest = self.get_table_name(table_base, flux_nom)
        pole_source = "Resine" if flux_nom == "3D" else "3D"
        type_dest = self.get_type_production(flux_nom)
        type_source = self.get_type_production(pole_source)
        table_source = self.get_table_name(table_base, pole_source)
        col_name = "reference_complete" if source == "Interne" else "reference_piece"

        try:
            with sqlite3.connect("atelier.db", timeout=30.0) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT 1 FROM {table_dest} WHERE type_production = ? AND {col_name} = ?", (type_dest, nom_pur))
                existe_dest = cursor.fetchone()

                if existe_dest:
                    if source == "Interne":
                        cursor.execute(f"""
                            UPDATE {table_dest}
                            SET statut = ?, quantite = ?, temps_unitaire = ?, quantite_conso = ?, consommable_lie = ?, date_lancement = NULL
                            WHERE type_production = ? AND {col_name} = ?
                        """, (statut_priorite, qte, temps, poids, conso, type_dest, nom_pur))
                    else:
                        cursor.execute(f"""
                            UPDATE {table_dest}
                            SET statut = ?, quantite = ?, echeance = ?, temps_unitaire = ?, quantite_conso = ?, consommable_lie = ?, date_lancement = NULL
                            WHERE type_production = ? AND {col_name} = ?
                        """, (statut_priorite, qte, echeance, temps, poids, conso, type_dest, nom_pur))
                else:
                    prefix, desig = "", ""
                    date_saisie = datetime.now().strftime("%d/%m/%Y %H:%M")
                    if source == "Interne":
                        cursor.execute(f"SELECT prefix, designation, date_creation FROM {table_source} WHERE type_production = ? AND {col_name} = ?", (type_source, nom_pur))
                        data = cursor.fetchone()
                        if data:
                            prefix, desig, date_saisie = data
                        cursor.execute(f"""
                            INSERT INTO {table_dest} (type_production, {col_name}, statut, quantite, temps_unitaire, quantite_conso, consommable_lie, prefix, designation, date_creation, date_lancement)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                        """, (type_dest, nom_pur, statut_priorite, qte, temps, poids, conso, prefix, desig, date_saisie))
                    else:
                        cursor.execute(f"SELECT designation, date_saisie FROM {table_source} WHERE type_production = ? AND {col_name} = ?", (type_source, nom_pur))
                        data = cursor.fetchone()
                        if data:
                            desig, date_saisie = data
                        cursor.execute(f"""
                            INSERT INTO {table_dest} (type_production, {col_name}, quantite, temps_unitaire, statut, date_saisie, echeance, consommable_lie, quantite_conso, designation, date_lancement)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                        """, (type_dest, nom_pur, qte, temps, statut_priorite, date_saisie, echeance, conso, poids, desig))

                cursor.execute(f"DELETE FROM {table_source} WHERE type_production = ? AND {col_name} = ?", (type_source, nom_pur))
                conn.commit()

            # Validation visuelle
            self.lbl_message.configure(text=f"✅ '{nom_pur}' envoyé dans {flux_nom} !", text_color="#10B981")
            self.after(4000, lambda: self.lbl_message.configure(text=""))
            
            # Réinitialisation
            self.charger_references()
            self.entry_echeance.delete(0, 'end')
            self.var_priorite.set("Dans le flux")
            self.sur_changement_priorite("Dans le flux")

            if self.fonction_rafraichir_global:
                self.fonction_rafraichir_global()

        except Exception as e:
            self.lbl_message.configure(text=f"❌ Erreur BDD: {e}", text_color=self.error_border)
            print("Erreur complète :", e)