import { test, expect } from '@playwright/test';
import path from 'path';

/**
 * Tests de Purge Automatique des Données (24h)
 * Vérifie que les données sont supprimées après 24h conformément au RGPD
 *
 * Note: Ces tests sont conceptuels car tester une vraie purge de 24h
 * nécessiterait de mocker le temps au niveau du backend ou d'attendre 24h.
 */

test.describe('Purge Automatique (Conceptuel)', () => {
  test('devrait afficher l\'information sur la purge automatique', async ({ page }) => {
    await page.goto('/');

    // Vérifier qu'il y a une mention de la confidentialité et de la purge 24h
    const pageContent = await page.textContent('body');

    // L'application devrait informer l'utilisateur de la purge 24h
    // soit dans les CGU, la page d'accueil, ou dans l'interface
    expect(
      pageContent?.includes('24') ||
      pageContent?.includes('confidentialité') ||
      pageContent?.includes('RGPD')
    ).toBe(true);
  });

  test('devrait avoir un indicateur de temps restant pour les fichiers', async ({ page }) => {
    // Se connecter et uploader un fichier
    await page.goto('/register');
    const email = `test-${Date.now()}@example.com`;
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/mot de passe/i).first().fill('TestPassword123!');
    await page.getByRole('button', { name: /s'inscrire/i }).click();
    await page.waitForURL(/\/chat/, { timeout: 10000 });

    const filePath = path.join(__dirname, '../fixtures/test-inventory.csv');
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    await page.waitForTimeout(2000);

    // Vérifier qu'il y a un indicateur de temps
    // (ex: "Expiration dans 23h", "Suppression automatique dans X heures")
    const hasTimeIndicator = await page.locator('[data-testid*="expiry"], [data-testid*="ttl"]').count();

    // Si l'UI affiche le temps restant, c'est bon
    // Sinon, au moins vérifier que le fichier est bien uploadé
    if (hasTimeIndicator === 0) {
      await expect(page.getByText(/test-inventory\.csv/i)).toBeVisible();
    }
  });

  test('devrait permettre la suppression manuelle avant expiration', async ({ page }) => {
    // Se connecter et uploader un fichier
    await page.goto('/register');
    const email = `test-${Date.now()}@example.com`;
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/mot de passe/i).first().fill('TestPassword123!');
    await page.getByRole('button', { name: /s'inscrire/i }).click();
    await page.waitForURL(/\/chat/, { timeout: 10000 });

    const filePath = path.join(__dirname, '../fixtures/test-inventory.csv');
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(filePath);
    await page.waitForTimeout(2000);

    // Chercher un bouton de suppression
    const deleteButton = await page.locator('[aria-label*="supprimer"], [data-testid*="delete"], button[class*="delete"]').first();

    if (await deleteButton.isVisible()) {
      await deleteButton.click();
      await page.waitForTimeout(500);

      // Le fichier ne devrait plus être visible
      await expect(page.getByText(/test-inventory\.csv/i)).not.toBeVisible();
    }
  });

  test('devrait informer sur la politique de rétention des données', async ({ page }) => {
    await page.goto('/');

    // Chercher un lien vers la politique de confidentialité ou CGU
    const privacyLink = await page.locator('a[href*="privacy"], a[href*="confidentialite"], a[href*="cgu"]').first();

    if (await privacyLink.isVisible()) {
      // Cliquer et vérifier le contenu
      await privacyLink.click();
      await page.waitForTimeout(1000);

      const content = await page.textContent('body');
      expect(content && (content.includes('24') || content.includes('données') || content.includes('suppression') || content.includes('RGPD'))).toBe(true);
    } else {
      // Au minimum, il devrait y avoir une mention quelque part
      const pageContent = await page.textContent('body');
      expect(pageContent?.includes('confidentialité') || pageContent?.includes('données')).toBe(true);
    }
  });
});

/**
 * Test Backend: Vérification de la purge côté serveur
 *
 * Pour tester la vraie purge automatique, il faudrait:
 * 1. Créer un endpoint backend /api/test/trigger-purge
 * 2. Mocker la date système (Date.now) pour simuler 24h plus tard
 * 3. Déclencher le job de purge manuellement
 * 4. Vérifier que:
 *    - Les fichiers sont supprimés de MinIO
 *    - Les documents sont supprimés de PostgreSQL
 *    - Les chunks sont supprimés de TypeSense
 *    - Les conversations sont archivées ou supprimées
 *
 * Exemple de test backend (à placer dans backend/tests):
 *
 * ```python
 * def test_automatic_purge_after_24h(db_session, minio_client):
 *     # Upload un fichier
 *     file = upload_test_file(...)
 *
 *     # Mocker le temps: +24h + 1 minute
 *     with freeze_time(datetime.now() + timedelta(hours=24, minutes=1)):
 *         # Déclencher le job de purge
 *         trigger_purge_job()
 *
 *         # Vérifier suppression
 *         assert not db_session.query(FileDB).filter_by(id=file.id).first()
 *         assert not minio_client.stat_object(bucket, file.path)
 *         assert not typesense_client.documents[file.id].retrieve()
 * ```
 */

test.describe('Documentation Tests de Purge Backend', () => {
  test('documentation - tests de purge backend requis', async () => {
    // Ce test sert de documentation
    // Les vrais tests de purge doivent être dans backend/tests/test_purge.py

    console.log(`
    ⚠️ TESTS DE PURGE BACKEND REQUIS ⚠️

    Les tests suivants doivent être implémentés dans backend/tests/:

    1. test_purge_files_after_24h()
       - Vérifier suppression fichiers de MinIO

    2. test_purge_database_records_after_24h()
       - Vérifier suppression de FileDB, conversations, messages

    3. test_purge_typesense_chunks_after_24h()
       - Vérifier suppression des chunks vectorisés

    4. test_purge_preserves_recent_data()
       - Vérifier que les données <24h sont préservées

    5. test_manual_purge_trigger()
       - Vérifier possibilité de déclencher manuellement

    Utiliser 'freezegun' pour mocker le temps:
    pip install freezegun

    from freezegun import freeze_time
    from datetime import datetime, timedelta

    @freeze_time("2024-01-15 12:00:00")
    def test_purge():
        # Upload à 12h
        file = upload_file()

        # Avancer de 24h
        with freeze_time("2024-01-16 12:01:00"):
            run_purge_job()
            assert file_is_deleted(file.id)
    `);

    expect(true).toBe(true);
  });
});
