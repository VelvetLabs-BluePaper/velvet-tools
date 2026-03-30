/**
 * Dynamic Navigator for VelvetLabs Social Media Agent
 * Uses dev-browser's snapshotForAI() to navigate dynamic menus
 *
 * Usage: dev-browser --connect http://localhost:9222 --timeout 60 run navigator.js
 * Or inline: dev-browser --connect --timeout 30 << 'EOF' ... EOF
 *
 * This module provides reusable functions for navigating complex UIs
 * like Meta Business Suite where URLs are not direct.
 */

// ============================================================
// Core navigation helpers
// ============================================================

/**
 * Wait for page to be interactive (no spinners/loaders)
 */
async function waitForStable(page, timeout = 5000) {
  await page.waitForLoadState("domcontentloaded");
  await page.waitForTimeout(1000);
  // Wait until no network activity for 500ms
  try {
    await page.waitForLoadState("networkidle", { timeout });
  } catch {
    // networkidle can timeout on heavy pages — that's ok
  }
}

/**
 * Get a concise snapshot focused on interactive elements
 * Filters out noise from navigation bars and footers
 */
async function getPageState(page) {
  const snapshot = await page.snapshotForAI();
  return {
    full: snapshot.full,
    url: page.url(),
    title: await page.title()
  };
}

/**
 * Find and click an element by its role and name
 * Handles scrolling into view automatically
 * Returns true if clicked, false if not found
 */
async function clickByRole(page, role, name, options = {}) {
  const { index = 0, force = false, timeout = 5000 } = options;
  try {
    const locator = page.getByRole(role, { name });
    const count = await locator.count();
    if (count === 0) return false;

    const target = count > 1 ? locator.nth(index) : locator;
    await target.scrollIntoViewIfNeeded();
    await page.waitForTimeout(200);
    await target.click({ force, timeout });
    return true;
  } catch (e) {
    console.warn(`clickByRole failed: ${role}/${name} — ${e.message}`);
    return false;
  }
}

/**
 * Find and click a menu item by navigating through a menu path
 * e.g., navigateMenu(page, ["Configuración", "Información de la empresa", "Ubicación"])
 */
async function navigateMenu(page, path, waitBetween = 1500) {
  for (const item of path) {
    console.log(`  → Clicking: "${item}"`);

    // Try multiple strategies
    let clicked = false;

    // Strategy 1: getByRole link/button/menuitem/tab
    for (const role of ["link", "button", "menuitem", "tab", "treeitem"]) {
      clicked = await clickByRole(page, role, item);
      if (clicked) break;
    }

    // Strategy 2: getByText exact match
    if (!clicked) {
      try {
        const textEl = page.getByText(item, { exact: true });
        if (await textEl.count() > 0) {
          await textEl.first().click();
          clicked = true;
        }
      } catch {}
    }

    // Strategy 3: getByText partial match
    if (!clicked) {
      try {
        const textEl = page.getByText(item);
        if (await textEl.count() > 0) {
          await textEl.first().click();
          clicked = true;
        }
      } catch {}
    }

    if (!clicked) {
      console.error(`  ✗ Could not find: "${item}"`);
      return false;
    }

    console.log(`  ✓ Clicked: "${item}"`);
    await page.waitForTimeout(waitBetween);
  }
  return true;
}

/**
 * Fill a form field by label
 */
async function fillField(page, label, value) {
  // Try textbox first, then combobox
  for (const role of ["textbox", "combobox"]) {
    try {
      const field = page.getByRole(role, { name: label });
      if (await field.count() > 0) {
        await field.fill(value);
        return true;
      }
    } catch {}
  }
  return false;
}

/**
 * Select from a dropdown by typing and clicking the option
 */
async function selectFromDropdown(page, label, searchText, optionText, waitMs = 1500) {
  const filled = await fillField(page, label, searchText);
  if (!filled) return false;

  await page.waitForTimeout(waitMs);

  // Click the matching option
  try {
    await page.getByText(optionText, { exact: false }).first().click();
    return true;
  } catch {
    // Try keyboard selection
    await page.keyboard.press("ArrowDown");
    await page.waitForTimeout(200);
    await page.keyboard.press("Enter");
    return true;
  }
}

/**
 * Close any modal/dialog that might be blocking
 */
async function dismissModal(page) {
  // Try Escape first
  await page.keyboard.press("Escape");
  await page.waitForTimeout(500);

  // Try clicking close buttons
  for (const label of ["Cerrar", "Close", "No, gracias", "Ahora no", "Cancelar"]) {
    const clicked = await clickByRole(page, "button", label);
    if (clicked) {
      await page.waitForTimeout(500);
      return true;
    }
  }
  return false;
}

/**
 * Take a screenshot and save it
 */
async function shot(page, name) {
  const buf = await page.screenshot();
  const path = await saveScreenshot(buf, `${name}.png`);
  console.log(`📸 ${name}.png`);
  return path;
}

// ============================================================
// Meta / Facebook specific helpers
// ============================================================

/**
 * Navigate to Meta Business Suite for a specific page
 */
async function goToMetaBusiness(page, assetId) {
  await page.goto(`https://business.facebook.com/latest/?asset_id=${assetId}`);
  await waitForStable(page);
  await dismissModal(page); // Instagram connection dialog often appears
}

/**
 * Create a Facebook Page
 */
async function createFacebookPage(page, { name, category, bio }) {
  await page.goto("https://www.facebook.com/pages/creation/");
  await waitForStable(page);

  // Fill name
  await fillField(page, "Nombre de la página (obligatorio)", name);
  await page.waitForTimeout(300);

  // Fill category
  await selectFromDropdown(page, "Categoría (obligatorio)", category, category);
  await page.waitForTimeout(500);

  // Fill bio if provided
  if (bio) {
    await fillField(page, "Presentación (opcional)", bio);
    await page.waitForTimeout(300);
  }

  // Click create
  const btn = page.getByRole("button", { name: "Crear página" });
  await btn.scrollIntoViewIfNeeded();
  await page.waitForTimeout(300);
  await btn.click();

  await page.waitForTimeout(5000);
  await shot(page, "page_created");

  return { url: page.url(), title: await page.title() };
}

// Export for use in scripts
// (In QuickJS sandbox, these are available as globals when this file is loaded)
console.log("Navigator loaded. Functions available: navigateMenu, clickByRole, fillField, selectFromDropdown, dismissModal, shot, createFacebookPage, goToMetaBusiness");
