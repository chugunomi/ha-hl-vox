/**
 * Half-Life VOX Phrase Builder card – autocomplete and repeatable clips.
 * Add as Lovelace resource: /hl_vox/hl-vox-phrase-builder.js (type: module)
 * Then add card type: custom:hl-vox-phrase-builder
 */
(function () {
  const CARD_TYPE = "hl-vox-phrase-builder";

  class HlVoxPhraseBuilderCard extends HTMLElement {
    constructor() {
      super();
      this.attachShadow({ mode: "open" });
      this._clips = [];
      this._phraseId = "";
      this._clipsList = [""];
      this._message = "";
      this._messageSuccess = false;
      this._loading = false;
    }

    setConfig() {}

    set hass(hass) {
      this._hass = hass;
      if (!this._clipsLoaded && hass) {
        this._clipsLoaded = true;
        this._fetchClips();
      } else {
        this._render();
      }
    }

    async _fetchClips() {
      if (!this._hass?.connection) return;
      this._loading = true;
      this._render();
      try {
        const res = await this._hass.connection.sendMessagePromise({
          type: "hl_vox/clips",
        });
        this._clips = res?.clips ?? [];
      } catch (e) {
        this._clips = [];
        this._message = "Failed to load clips";
        this._messageSuccess = false;
      }
      this._loading = false;
      this._render();
    }

    _render() {
      const hass = this._hass;
      const clips = this._clips;
      const phraseId = this._phraseId;
      const clipsList = this._clipsList;
      const loading = this._loading;
      const message = this._message;
      const success = this._messageSuccess;

      const datalistId = "hl-vox-clips-datalist";
      const options =
        clips.length > 0
          ? clips
              .map(
                (c) =>
                  `<option value="${this._escapeHtml(c)}">${this._escapeHtml(c)}</option>`
              )
              .join("")
          : "";

      this.shadowRoot.innerHTML = `
<style>
  ha-card {
    padding: 16px;
  }
  .field { margin-bottom: 12px; }
  .field label { display: block; margin-bottom: 4px; font-weight: 500; }
  input[type="text"] {
    width: 100%;
    max-width: 280px;
    padding: 8px;
    box-sizing: border-box;
  }
  .row {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
  }
  .row input { flex: 1; max-width: 240px; }
  mwc-button, button {
    margin-right: 8px;
    margin-top: 8px;
  }
  .message { margin-top: 12px; padding: 8px; border-radius: 4px; }
  .message.success { background: var(--success-color); color: var(--text-primary-color); }
  .message.error { background: var(--error-color); color: white; }
  .loading { opacity: 0.7; }
</style>
<ha-card>
  <div class="${loading ? "loading" : ""}">
    <div class="field">
      <label>Phrase ID</label>
      <input type="text" id="phrase-id" placeholder="e.g. leak_detected" value="${this._escapeHtml(phraseId)}" list="${datalistId}" />
    </div>
    <datalist id="${datalistId}">${options}</datalist>
    <div class="field">
      <label>Clips (order matters; same clip can repeat)</label>
      ${clipsList
        .map(
          (val, i) => `
        <div class="row" data-row="${i}">
          <input type="text" data-row="${i}" value="${this._escapeHtml(val)}" list="${datalistId}" placeholder="Type to search..." />
          <button type="button" data-action="remove" data-row="${i}">Remove</button>
        </div>`
        )
        .join("")}
      <button type="button" data-action="add">Add clip</button>
    </div>
    <button type="button" data-action="save">Save phrase</button>
    ${message ? `<div class="message ${success ? "success" : "error"}">${this._escapeHtml(message)}</div>` : ""}
  </div>
</ha-card>`;

      const phraseInput = this.shadowRoot.getElementById("phrase-id");
      if (phraseInput) {
        phraseInput.addEventListener("input", (e) => {
          this._phraseId = e.target.value;
        });
      }

      this.shadowRoot.querySelectorAll("input[data-row]").forEach((input) => {
        const row = parseInt(input.dataset.row, 10);
        input.addEventListener("input", (e) => {
          this._clipsList[row] = e.target.value;
        });
      });

      this.shadowRoot.querySelectorAll("[data-action=remove]").forEach((btn) => {
        const row = parseInt(btn.dataset.row, 10);
        btn.addEventListener("click", () => {
          this._clipsList.splice(row, 1);
          if (this._clipsList.length === 0) this._clipsList.push("");
          this._render();
        });
      });

      const addBtn = this.shadowRoot.querySelector("[data-action=add]");
      if (addBtn) {
        addBtn.addEventListener("click", () => {
          this._clipsList.push("");
          this._render();
        });
      }

      const saveBtn = this.shadowRoot.querySelector("[data-action=save]");
      if (saveBtn) {
        saveBtn.addEventListener("click", () => this._save());
      }
    }

    _escapeHtml(s) {
      if (s == null) return "";
      const div = document.createElement("div");
      div.textContent = s;
      return div.innerHTML;
    }

    async _save() {
      const phraseId = this._phraseId.trim().replace(/\s+/g, "_");
      const clips = this._clipsList.map((s) => s.trim()).filter(Boolean);
      if (!phraseId) {
        this._message = "Enter a phrase ID";
        this._messageSuccess = false;
        this._render();
        return;
      }
      if (clips.length === 0) {
        this._message = "Add at least one clip";
        this._messageSuccess = false;
        this._render();
        return;
      }
      try {
        await this._hass.callService("hl_vox", "set_phrase", {
          phrase_id: phraseId,
          clips: clips,
        });
        this._message = "Phrase saved.";
        this._messageSuccess = true;
      } catch (e) {
        this._message = e?.message || "Failed to save";
        this._messageSuccess = false;
      }
      this._render();
    }

    getCardSize() {
      return 4;
    }
  }

  customElements.define(CARD_TYPE, HlVoxPhraseBuilderCard);

  window.customCards = window.customCards || [];
  window.customCards.push({
    type: CARD_TYPE,
    name: "Half-Life VOX Phrase Builder",
    description: "Build VOX phrases with autocomplete and repeating clips.",
    preview: false,
  });
})();
