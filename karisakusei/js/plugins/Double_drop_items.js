/*:
 * @target MZ
 * @plugindesc NUUN_AddDropItemsの追加ドロップを倍化するプラグイン
 * @base NUUN_AddDropItems
 * @orderAfter NUUN_AddDropItems
 * @version 1.0.0
 * @author 野獣先輩
 *
 * @param DoubleStateId
 * @text 倍化ステートID
 * @desc ドロップ倍化効果を付与するステートのID
 * @type state
 * @default 35
 *
 * @help
 * このプラグインを導入すると、バトル終了時に
 * パーティーメンバーの誰かが指定のステートを
 * 所持している場合、ドロップアイテムがすべて倍になります。
 *
 * 【使用例】
 * 1. 本プラグインとNUUN_AddDropItems.jsを
 *    プラグインマネージャーに追加し、有効化。
 * 2. パラメータ「倍化ステートID」をステートID 35に設定。
 * 3. データベースのポーションアイテムに
 *    「ステートの追加：35」を設定。
 * 4. 戦闘中にそのポーションを使うと、戦闘後の
 *    ドロップがすべて2倍になります。
 *
 * 必要プラグイン: NUUN_AddDropItems
 */
(() => {
    const pluginName = document.currentScript.src.split('/').pop();
    const params = PluginManager.parameters(pluginName);
    const doubleStateId = Number(params['DoubleStateId'] || 35);

    const _Game_Enemy_makeDropItems = Game_Enemy.prototype.makeDropItems;
    Game_Enemy.prototype.makeDropItems = function() {
        let drops = _Game_Enemy_makeDropItems.call(this);
        if ($gameParty.members().some(actor => actor.isStateAffected(doubleStateId))) {
            // 元のドロップを重複して追加（2倍化）
            drops = drops.concat(drops);
        }
        return drops;
    };
})();
