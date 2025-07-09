/*:
 * @target MZ
 * @plugindesc 特定アイテムだけ所持上限を99個以上にできるプラグイン（メモ欄制御） - by 鈴木
 * @author 鈴木
 * 
 * @help
 * ▼使い方：
 * アイテムのメモ欄に以下を記入してください：
 * 
 * <MaxStack:999>   ← このアイテムは最大999個まで所持可能になります
 *
 * 特にメモを記入しない場合は通常通り99個までです。
 */

(() => {
  // アイテムごとの最大所持数を取得
  const getMaxItemNumber = function(item) {
    if (!item) return 0;
    if (item.meta.MaxStack) {
      return Number(item.meta.MaxStack) || 99;
    }
    return 99;
  };

  // 上限チェックの上書き
  const _GameParty_maxItems = Game_Party.prototype.maxItems;
  Game_Party.prototype.maxItems = function(item) {
    if (DataManager.isItem(item)) {
      return getMaxItemNumber(item);
    }
    return _GameParty_maxItems.call(this, item);
  };
})();
