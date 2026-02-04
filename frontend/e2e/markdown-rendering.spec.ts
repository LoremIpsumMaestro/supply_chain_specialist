import { test, expect } from '@playwright/test'

test.describe('Markdown Rendering in Chat', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the app and ensure we're logged in
    await page.goto('/')

    // TODO: Add login flow when authentication is implemented
    // For now, we'll assume the user is already authenticated or auth is disabled
  })

  test('should render markdown table correctly', async ({ page }) => {
    // Navigate to chat
    await page.goto('/chat')

    // Wait for chat to load
    await expect(page.locator('text=Bienvenue')).toBeVisible({ timeout: 10000 })

    // Type a message that would trigger a markdown table response
    const input = page.locator('textarea[placeholder*="message"]').first()
    await input.fill('Test markdown table')
    await input.press('Enter')

    // For testing, we can inject a markdown table directly into the chat
    // In a real scenario, this would come from the LLM response
    await page.evaluate(() => {
      const mockTableResponse = `
| Produit | Stock | Statut |
|---------|-------|--------|
| Item A  | 150   | OK     |
| Item B  | 5     | Alerte |
      `.trim()

      // Simulate adding a message with markdown
      // This is a mock - in reality this would come from the backend
      console.log('Mock table response:', mockTableResponse)
    })

    // Note: This test needs a real backend response with markdown
    // or a way to mock the streaming response
  })

  test('should render code blocks with syntax highlighting', async ({ page }) => {
    await page.goto('/chat')

    await expect(page.locator('text=Bienvenue')).toBeVisible({ timeout: 10000 })

    // In a real test, we would trigger an LLM response with a code block
    // For now, this is a placeholder
  })

  test('should render ordered and unordered lists', async ({ page }) => {
    await page.goto('/chat')

    await expect(page.locator('text=Bienvenue')).toBeVisible({ timeout: 10000 })

    // In a real test, we would trigger an LLM response with lists
    // For now, this is a placeholder
  })

  test('should render blockquotes', async ({ page }) => {
    await page.goto('/chat')

    await expect(page.locator('text=Bienvenue')).toBeVisible({ timeout: 10000 })

    // In a real test, we would trigger an LLM response with blockquotes
    // For now, this is a placeholder
  })

  test('should make tables horizontally scrollable on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('/chat')

    await expect(page.locator('text=Bienvenue')).toBeVisible({ timeout: 10000 })

    // In a real test, we would verify that tables have overflow-x-auto
    // and can be scrolled horizontally on mobile
  })

  test('should render streaming messages with markdown', async ({ page }) => {
    await page.goto('/chat')

    await expect(page.locator('text=Bienvenue')).toBeVisible({ timeout: 10000 })

    // In a real test, we would verify that partial markdown renders gracefully
    // during streaming and completes properly when done
  })

  test('should not render HTML tags (XSS prevention)', async ({ page }) => {
    await page.goto('/chat')

    await expect(page.locator('text=Bienvenue')).toBeVisible({ timeout: 10000 })

    // In a real test, we would inject a message with HTML/script tags
    // and verify they are escaped and not executed
  })

  test('user messages should display as plain text', async ({ page }) => {
    await page.goto('/chat')

    await expect(page.locator('text=Bienvenue')).toBeVisible({ timeout: 10000 })

    const input = page.locator('textarea[placeholder*="message"]').first()
    await input.fill('**This should not be bold** and `this should not be code`')
    await input.press('Enter')

    // Wait for message to appear
    await page.waitForTimeout(1000)

    // Verify user message displays markdown syntax literally (not rendered)
    // The text should contain the actual ** and ` characters
    const userMessage = page.locator('text=**This should not be bold**').first()
    await expect(userMessage).toBeVisible()
  })
})
