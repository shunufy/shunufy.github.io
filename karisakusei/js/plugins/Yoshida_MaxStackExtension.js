
/*:
 * @target MZ
 * @plugindesc 所持アイテムの上限を特定アイテムの所持で拡張する（吉田）ver1.0
 * @author 吉田
 * 
 * @help
 * アイテムID50（拡張アイテム）を持っていると、ID32のアイテム（珠）の
 * 所持上限が999に拡張されます。
 * それ以外のアイテムは通常通り最大99個です。
 *
 * 利用方法：
 * - js/plugins/ にこのファイルを入れる
 * - RPGツクールMZのプラグイン管理で有効化
 * 
 * 利用条件：
 * - 商用・非商用問わず利用可、クレジット任意
 */

(() => {
  const originalMaxItems = Game_Party.prototype.maxItems;
  Game_Party.prototype.maxItems = function(item) {
    if (DataManager.isItem(item)) {
      // アイテムID32（珠）の所持上限を条件付きで拡張
      if (item.id === 32 && this.hasItem($dataItems[50], false)) {
        return 999; // ID50を持っていると999まで持てる
      }

      // MaxStackタグが設定されている場合はそれを使用
      if (item.meta.MaxStack) {
        return Number(item.meta.MaxStack) || 99;
      }
    }
    return 99;
  };
})();
