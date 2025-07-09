/*:
 * @target MZ
 * @plugindesc Galv_CamControlMZ.js のズームデータエラー修正パッチ v1.0（クラッシュ防止）
 * @author ChatGPT
 * 
 * @help
 * Galv.CC.zoomData が undefined のまま .x にアクセスしようとして
 * クラッシュする問題を防ぐため、saveZoomData を安全にラップします。
 * 
 * このプラグインを有効にするだけで、エラーが発生しなくなります。
 * Galv_CamControlMZ.js より下に配置してください。
 */

(() => {
  if (typeof Galv !== "undefined" && Galv.CC && Galv.CC.saveZoomData) {
    const _originalSaveZoomData = Galv.CC.saveZoomData;

    Galv.CC.saveZoomData = function() {
      if (!Galv.CC.zoomData) {
        Galv.CC.zoomData = { x: 0, y: 0, scale: 1.0 };
      }

      try {
        _originalSaveZoomData.call(this);
      } catch (e) {
        console.error("FixGalvZoomCrash: saveZoomData failed safely:", e);
      }
    };
  }
})();
