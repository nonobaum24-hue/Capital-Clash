import pygame
import sys
from settings import settings
from setting_menu import settings_loop

def test_settings():
    """Test Settings-Funktionalität"""
    print("=" * 50)
    print("TEST: Settings Funktionalität")
    print("=" * 50)
    
    # 1. Settings laden
    print("\n1. Settings werden geladen...")
    game_settings = settings()
    print(f"   ✓ Auflösung: {game_settings.width}x{game_settings.height}")
    print(f"   ✓ Master Volume: {game_settings.master_volume}")
    print(f"   ✓ Musik Volume: {game_settings.music_volume}")
    print(f"   ✓ SFX Volume: {game_settings.sfx_volume}")
    
    # 2. Settings ändern
    print("\n2. Settings werden geändert...")
    game_settings.width = 1920
    game_settings.height = 1080
    game_settings.master_volume = 75
    game_settings.music_volume = 80
    game_settings.sfx_volume = 70
    print(f"   ✓ Neue Auflösung: {game_settings.width}x{game_settings.height}")
    print(f"   ✓ Neuer Master Volume: {game_settings.master_volume}")
    
    # 3. Settings speichern
    print("\n3. Settings werden gespeichert...")
    game_settings.save_settings()
    print(f"   ✓ Datei gespeichert: {game_settings.settings_file}")
    
    # 4. Neue Instanz laden und prüfen
    print("\n4. Neue Settings-Instanz wird geladen (Speicher-Test)...")
    game_settings2 = settings()
    print(f"   ✓ Auflösung: {game_settings2.width}x{game_settings2.height}")
    print(f"   ✓ Master Volume: {game_settings2.master_volume}")
    
    if (game_settings2.width == 1920 and 
        game_settings2.height == 1080 and 
        game_settings2.master_volume == 75):
        print("\n✅ ALLE TESTS BESTANDEN!")
        return True
    else:
        print("\n❌ TEST FEHLGESCHLAGEN!")
        return False

def test_with_menu():
    """Test mit Settings-Menu GUI"""
    print("\n" + "=" * 50)
    print("TEST: Settings-Menu GUI")
    print("=" * 50)
    
    pygame.init()
    game_settings = settings()
    
    # Fenster mit gespeicherten Einstellungen erstellen
    screen = pygame.display.set_mode((game_settings.width, game_settings.height))
    pygame.display.set_caption("Capital Crush - Settings Test")
    
    print(f"\n✓ Pygame initialisiert")
    print(f"✓ Fenster erstellt: {game_settings.width}x{game_settings.height}")
    print(f"\nÖffne das Settings-Menu...")
    print("(Stelle die Werte ein und klicke 'Speichern' oder 'Zurück')\n")
    
    settings_loop(game_settings, screen)
    
    # Nach dem Menu neue Einstellungen laden
    print("\n✓ Settings-Menu geschlossen")
    print(f"✓ Neue Auflösung: {game_settings.width}x{game_settings.height}")
    print(f"✓ Master Volume: {game_settings.master_volume}")
    
    pygame.quit()
    print("\n✅ Menu-Test abgeschlossen!")

if __name__ == "__main__":
    # Test 1: Funktionalität
    success = test_settings()
    
    if success:
        # Test 2: GUI Menu (optional)
        try:
            response = input("\nMöchtest du das Settings-Menu testen? (j/n): ").lower()
            if response == 'j':
                test_with_menu()
        except KeyboardInterrupt:
            print("\nTest abgebrochen.")
        except Exception as e:
            print(f"\n❌ Fehler beim Menu-Test: {e}")
    
    print("\n" + "=" * 50)
    print("Tests beendet!")
    print("=" * 50)
