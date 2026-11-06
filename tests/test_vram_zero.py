"""Tests sans carte graphique : classification, echec de collecte, PID reutilise.
Lancer :  python -m unittest discover -s tests -v
"""
import importlib.machinery
import importlib.util
import os
import unittest

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "vram_zero.pyw")
_loader = importlib.machinery.SourceFileLoader("vram_zero", SRC)
_spec = importlib.util.spec_from_loader("vram_zero", _loader)
vz = importlib.util.module_from_spec(_spec)
_loader.exec_module(vz)


class Classification(unittest.TestCase):
    def test_programme_inconnu_n_est_plus_masque(self):
        # Forge tourne sous python.exe : visible a part (unknown), jamais "red"
        self.assertEqual(vz.classify(r"C:\StudioAI\forge\venv\Scripts\python.exe"), "unknown")

    def test_nom_illisible(self):
        self.assertEqual(vz.classify("[Insufficient Permissions]"), "noid")

    def test_systeme_critique_avant_mots_cles_ia(self):
        self.assertEqual(vz.classify(r"C:\Users\x\ollama\dwm.exe"), "red")

    def test_ia_reconnue(self):
        self.assertEqual(vz.classify(r"C:\Users\x\AppData\Local\Programs\Ollama\ollama.exe"), "green")

    def test_protege(self):
        self.assertTrue(vz.is_protected(r"C:\Program Files\WindowsApps\Claude_4\app\claude.exe"))
        self.assertTrue(vz.is_protected(r"C:\Program Files\Docker\Docker\Docker Desktop.exe"))
        self.assertFalse(vz.is_protected(r"C:\x\ollama.exe"))


class Collecte(unittest.TestCase):
    def test_echec_nvidia_smi_n_est_pas_une_liste_vide(self):
        old = vz.run_cmd
        try:
            vz.run_cmd = lambda args: None
            self.assertIsNone(vz.get_gpu_processes())
            self.assertIsNone(vz.get_gpu_stats())
        finally:
            vz.run_cmd = old

    def test_aucun_processus_est_une_liste_vide(self):
        old = vz.run_cmd
        try:
            vz.run_cmd = lambda args: ""
            self.assertEqual(vz.get_gpu_processes(), [])
        finally:
            vz.run_cmd = old


class FermetureSure(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.killer = lambda pid: (self.calls.append(pid) or (True, ""))

    def proc(self, pid, name):
        return {"pid": pid, "name": name, "level": "green", "protected": False}

    def test_pid_reutilise_n_est_pas_ferme(self):
        cible = self.proc(100, r"C:\x\ollama.exe")
        actuel = [self.proc(100, r"C:\Windows\explorer.exe")]
        res = vz.safe_kill([cible], lister=lambda: actuel, killer=self.killer)
        self.assertEqual(res[0][1], "changed")
        self.assertEqual(self.calls, [])

    def test_liste_non_verifiable_ne_ferme_rien(self):
        res = vz.safe_kill([self.proc(100, "a.exe")], lister=lambda: None, killer=self.killer)
        self.assertEqual(res[0][1], "unverified")
        self.assertEqual(self.calls, [])

    def test_meme_pid_meme_nom_est_ferme(self):
        p = self.proc(100, r"C:\x\ollama.exe")
        res = vz.safe_kill([p], lister=lambda: [dict(p)], killer=self.killer)
        self.assertEqual(res[0][1], "closed")
        self.assertEqual(self.calls, [100])

    def test_processus_deja_parti(self):
        res = vz.safe_kill([self.proc(100, "a.exe")], lister=lambda: [], killer=self.killer)
        self.assertEqual(res[0][1], "gone")


if __name__ == "__main__":
    unittest.main()
