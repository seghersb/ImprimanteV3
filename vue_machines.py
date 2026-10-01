import customtkinter as ctk
import sqlite3

class FenetreAjoutMachine(ctk.CTkToplevel):
    def __init__(self, master, callback_succes):
        super().__init__(master)
        self.callback_succes = callback_succes

        self.title("Ajouter une machine")
        self.geometry("450x450")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="➕ Nouvelle Machine", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        # Nom
        frame_nom = ctk.CTkFrame(self, fg_color="transparent")
        frame_nom.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(frame_nom, text="Nom de la machine :").pack(side="left", padx=5)
        self.entry_nom = ctk.CTkEntry(frame_nom, width=220, placeholder_text="Ex: Imprimante 3D - 01")
        self.entry_nom.pack(side="right", padx=5)

        # Secteurs autorisés
        ctk.CTkLabel(self, text="Secteurs autorisés :", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=25, pady=(15, 5))
        
        self.scroll_chk = ctk.CTkScrollableFrame(self, height=180)
        self.scroll_chk.pack(fill="x", padx=20, pady=5)
        
        self.check_vars = []
        self.charger_checkboxes_secteurs()

        self.lbl_message = ctk.CTkLabel(self, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_message.pack(pady=5)

        ctk.CTkButton(self, text="Enregistrer", fg_color="#10B981", hover_color="#059669", command=self.enregistrer).pack(pady=15)

    def charger_checkboxes_secteurs(self):
        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        secteurs_dict = {}
        try:
            # Les secteurs sont stockés avec les paramètres de références.
            cursor.execute("SELECT prefix, nom FROM parametres_references WHERE type_production = '3D' AND nature = 'secteur'")
            for prefix, nom in cursor.fetchall():
                if prefix: 
                    secteurs_dict[prefix] = f"{prefix} - {nom}"
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()

        var_all = ctk.StringVar(value="ALL")
        chk_all = ctk.CTkCheckBox(self.scroll_chk, text="🟢 TOUT ACCEPTER (ALL)", variable=var_all, onvalue="ALL", offvalue="")
        chk_all.pack(anchor="w", padx=5, pady=5)
        self.check_vars.append(("ALL", var_all))

        # Tri alphabétique par le nom du secteur
        for prefix, texte in sorted(secteurs_dict.items(), key=lambda x: x[1]):
            var = ctk.StringVar(value="")
            chk = ctk.CTkCheckBox(self.scroll_chk, text=texte, variable=var, onvalue=prefix, offvalue="")
            chk.pack(anchor="w", padx=5, pady=5)
            self.check_vars.append((prefix, var))

    def enregistrer(self):
        nom = self.entry_nom.get().strip()
        if not nom:
            self.lbl_message.configure(text="⚠️ Nom obligatoire.", text_color="orange")
            return

        selection = [var.get() for prefix, var in self.check_vars if var.get() != ""]
        if not selection:
            self.lbl_message.configure(text="⚠️ Cochez au moins un secteur.", text_color="orange")
            return

        prefixes_propres = "ALL" if "ALL" in selection else ",".join(selection)

        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO machines (type_production, nom, statut, prefixes_autorises) VALUES ('3D', ?, ?, ?)", (nom, "ON", prefixes_propres))
            conn.commit()
        except Exception as e:
            self.lbl_message.configure(text=f"❌ Erreur: {e}", text_color="red")
            conn.close()
            return
        finally:
            conn.close()

        if self.callback_succes:
            self.callback_succes()
        self.destroy()

class FenetreModifierNomMachine(ctk.CTkToplevel):
    def __init__(self, master, machine_id, nom_actuel, callback_succes):
        super().__init__(master)
        self.machine_id = machine_id
        self.callback_succes = callback_succes

        self.title("Modifier la machine")
        self.geometry("350x200")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text="✏️ Modifier le nom", font=ctk.CTkFont(size=18, weight="bold")).pack(pady=15)

        frame_nom = ctk.CTkFrame(self, fg_color="transparent")
        frame_nom.pack(fill="x", padx=20, pady=10)
        
        self.entry_nom = ctk.CTkEntry(frame_nom, width=250)
        self.entry_nom.insert(0, nom_actuel)
        self.entry_nom.pack(pady=5)

        self.lbl_message = ctk.CTkLabel(self, text="", font=ctk.CTkFont(weight="bold"))
        self.lbl_message.pack(pady=2)

        ctk.CTkButton(self, text="Enregistrer", fg_color="#10B981", hover_color="#059669", command=self.enregistrer).pack(pady=10)

    def enregistrer(self):
        nom = self.entry_nom.get().strip()
        if not nom:
            self.lbl_message.configure(text="⚠️ Nom obligatoire.", text_color="orange")
            return

        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE machines SET nom = ? WHERE id = ? AND type_production = '3D'", (nom, self.machine_id))
            conn.commit()
        except Exception as e:
            self.lbl_message.configure(text=f"❌ Erreur: {e}", text_color="red")
        finally:
            conn.close()

        if self.callback_succes:
            self.callback_succes()
        self.destroy()

class OptionMenuMultiple(ctk.CTkFrame):
    def __init__(self, master, prefixes_actuels, callback_changement):
        super().__init__(master, fg_color="transparent")
        
        if not prefixes_actuels:
            self.prefixes_actuels = []
        elif prefixes_actuels == "ALL":
            self.prefixes_actuels = "ALL"
        else:
            self.prefixes_actuels = [p.strip() for p in prefixes_actuels.split(",")]
        
        self.callback_changement = callback_changement

        texte_btn = "🟢 TOUS (ALL)" if self.prefixes_actuels == "ALL" else f"{len(self.prefixes_actuels)} secteur(s)"
        self.btn_menu = ctk.CTkButton(self, text=texte_btn, width=160, height=24, fg_color="#333333", command=self.ouvrir_popup)
        self.btn_menu.pack()

    def ouvrir_popup(self):
        popup = ctk.CTkToplevel(self)
        popup.title("Modifier les secteurs")
        popup.geometry("350x400")
        popup.resizable(False, False)
        popup.grab_set()

        ctk.CTkLabel(popup, text="Sélectionnez les secteurs :", font=ctk.CTkFont(weight="bold")).pack(pady=10)

        scroll = ctk.CTkScrollableFrame(popup, height=270)
        scroll.pack(fill="x", padx=10, pady=5)

        # Relecture des secteurs configurés.
        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        secteurs_dict = {}
        try:
            cursor.execute("SELECT prefix, nom FROM parametres_references WHERE type_production = '3D' AND nature = 'secteur'")
            for prefix, nom in cursor.fetchall():
                if prefix:
                    secteurs_dict[prefix] = f"{prefix} - {nom}"
        except sqlite3.OperationalError:
            pass
        finally:
            conn.close()

        vars_dict = {}
        
        var_all = ctk.StringVar(value="ALL" if self.prefixes_actuels == "ALL" else "")
        chk_all = ctk.CTkCheckBox(scroll, text="🟢 TOUS (ALL)", variable=var_all, onvalue="ALL", offvalue="")
        chk_all.pack(anchor="w", padx=5, pady=5)
        vars_dict["ALL"] = var_all

        for prefix, texte in sorted(secteurs_dict.items(), key=lambda x: x[1]):
            est_coche = prefix in self.prefixes_actuels or self.prefixes_actuels == "ALL"
            var = ctk.StringVar(value=prefix if est_coche else "")
            chk = ctk.CTkCheckBox(scroll, text=texte, variable=var, onvalue=prefix, offvalue="")
            chk.pack(anchor="w", padx=5, pady=5)
            vars_dict[prefix] = var

        def valider_modif():
            selection = [v.get() for k, v in vars_dict.items() if v.get() != ""]
            if not selection: return
            nouveaux_prefixes = "ALL" if "ALL" in selection else ",".join(selection)
            self.callback_changement(nouveaux_prefixes)
            popup.destroy()

        ctk.CTkButton(popup, text="Valider", fg_color="#10B981", command=valider_modif).pack(pady=10)

class OngletMachines(ctk.CTkFrame):
    def __init__(self, master, fonction_rafraichir_global=None):
        super().__init__(master, fg_color="transparent")
        self.fonction_rafraichir_global = fonction_rafraichir_global

        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(header_frame, text="⚙️ Gestion du Parc Machines", font=ctk.CTkFont(size=22, weight="bold")).pack(side="left")
        
        ctk.CTkButton(header_frame, text="🔄 Actualiser", width=110, fg_color="#374151", hover_color="#1F2937", command=self.charger_machines).pack(side="right", padx=5)
        ctk.CTkButton(header_frame, text="➕ Ajouter une machine", fg_color="#10B981", hover_color="#059669", command=self.ouvrir_fenetre_ajout).pack(side="right", padx=5)

        self.scroll_machines = ctk.CTkScrollableFrame(self)
        self.scroll_machines.pack(fill="both", expand=True, padx=5, pady=5)

        self.charger_machines()

    def ouvrir_fenetre_ajout(self):
        FenetreAjoutMachine(self, callback_succes=self.rafraichir_apres_ajout)

    def ouvrir_fenetre_modif_nom(self, machine_id, nom_actuel):
        FenetreModifierNomMachine(self, machine_id, nom_actuel, callback_succes=self.rafraichir_apres_ajout)

    def rafraichir_apres_ajout(self):
        self.charger_machines()
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()

    def toggle_statut(self, machine_id):
        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("SELECT statut FROM machines WHERE id = ? AND type_production = '3D'", (machine_id,))
        res = cursor.fetchone()
        if res:
            nouveau = "OFF" if res[0] == "ON" else "ON"
            cursor.execute("UPDATE machines SET statut = ? WHERE id = ? AND type_production = '3D'", (nouveau, machine_id))
            conn.commit()
        conn.close()

        self.charger_machines()
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()

    def supprimer_machine(self, machine_id):
        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM machines WHERE id = ? AND type_production = '3D'", (machine_id,))
        conn.commit()
        conn.close()

        self.charger_machines()
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()

    def modifier_secteurs_machine(self, machine_id, nouveaux_prefixes):
        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("UPDATE machines SET prefixes_autorises = ? WHERE id = ? AND type_production = '3D'", (nouveaux_prefixes, machine_id))
        conn.commit()
        conn.close()

        self.charger_machines()
        if self.fonction_rafraichir_global:
            self.fonction_rafraichir_global()

    def charger_machines(self):
        for widget in self.scroll_machines.winfo_children():
            widget.destroy()

        conn = sqlite3.connect("atelier.db", timeout=5.0)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, nom, statut, prefixes_autorises FROM machines WHERE type_production = '3D' ORDER BY id")
            machines_db = cursor.fetchall()
            
            if not machines_db:
                machines_defaut = [(f"Machine {i+1}", "ON", "ALL") for i in range(8)]
                cursor.executemany("INSERT INTO machines (type_production, nom, statut, prefixes_autorises) VALUES ('3D', ?, ?, ?)", machines_defaut)
                conn.commit()
                cursor.execute("SELECT id, nom, statut, prefixes_autorises FROM machines WHERE type_production = '3D' ORDER BY id")
                machines_db = cursor.fetchall()

        except sqlite3.OperationalError:
            machines_db = []
        finally:
            conn.close()

        if not machines_db:
            ctk.CTkLabel(self.scroll_machines, text="Aucune machine enregistrée.", font=ctk.CTkFont(slant="italic")).pack(pady=20)
            return

        for m_id, nom, statut, prefixes in machines_db:
            ligne = ctk.CTkFrame(self.scroll_machines, fg_color=("gray90", "gray15"))
            ligne.pack(fill="x", pady=5, ipadx=10, ipady=10)

            couleur_statut = "#10B981" if statut == "ON" else "#DC2626"
            pastille = "🟢" if statut == "ON" else "🔴"
            
            info_frame = ctk.CTkFrame(ligne, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True)

            titre_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            titre_frame.pack(anchor="w", padx=10, pady=(0, 5))
            
            ctk.CTkLabel(titre_frame, text=f"{pastille} {nom}", font=ctk.CTkFont(weight="bold", size=15), text_color=couleur_statut).pack(side="left")
            ctk.CTkButton(titre_frame, text="✏️", width=30, height=24, fg_color="transparent", text_color="#D1D5DB", hover_color="gray30",
                          command=lambda mid=m_id, n=nom: self.ouvrir_fenetre_modif_nom(mid, n)).pack(side="left", padx=10)
            
            frame_dropdown = ctk.CTkFrame(info_frame, fg_color="transparent")
            frame_dropdown.pack(anchor="w", padx=10)
            ctk.CTkLabel(frame_dropdown, text="Secteurs :", font=ctk.CTkFont(size=12, slant="italic")).pack(side="left", padx=(0, 5))
            
            menu_multi = OptionMenuMultiple(frame_dropdown, prefixes, lambda nvx, mid=m_id: self.modifier_secteurs_machine(mid, nvx))
            menu_multi.pack(side="left")

            btn_frame = ctk.CTkFrame(ligne, fg_color="transparent")
            btn_frame.pack(side="right", padx=10)

            texte_toggle = "HORS SERVICE" if statut == "ON" else "EN SERVICE"
            couleur_toggle = "#D97706" if statut == "ON" else "#2563EB"
            
            ctk.CTkButton(btn_frame, text=texte_toggle, fg_color=couleur_toggle, width=130, 
                          command=lambda i=m_id: self.toggle_statut(i)).pack(side="left", padx=5)
            
            ctk.CTkButton(btn_frame, text="🗑️", fg_color="#DC2626", hover_color="#991B1B", width=40,
                          command=lambda i=m_id: self.supprimer_machine(i)).pack(side="left", padx=5)