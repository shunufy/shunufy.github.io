/*:
 * @target MZ
 * @plugindesc 本来のドロップ枠に加えて追加ドロップスロットを確率で実現するプラグイン
 * @author Yoshida
 *
 * @param ExtraSlots
 * @text 追加ドロップスロット数
 * @desc 一度の戦闘で各敵につき追加でドロップ判定を行うスロット数を指定します
 * @type number
 * @min 0
 * @default 1
 *
 * @help
 * このプラグインを導入すると、各敵が本来ドロップするアイテムに加えて
 * パラメータで指定した数の追加スロットによるドロップ判定を行います。
 * 追加スロットは敵データベースのドロップリストを対象に、
 * 各スロットごとにランダムなアイテムを選択し、ドロップ率を考慮して配布します。
 *
 * <使い方>
 * 1. プラグインマネージャーにこのプラグインを追加し、有効化します。
 * 2. パラメータ「追加ドロップスロット数」を設定します。
 * 3. 通常のドロップ枠に加えて、指定数分の追加ドロップ判定が行われます。
 *
 */
(() => {
    const pluginName = document.currentScript.src.split('/').pop();
    const parameters = PluginManager.parameters(pluginName);
    const extraSlots = Number(parameters['ExtraSlots'] || 0);

    // 元のドロップ取得を保持
    const _Game_Enemy_makeDropItems = Game_Enemy.prototype.makeDropItems;
    Game_Enemy.prototype.makeDropItems = function() {
        // 本来のドロップ
        const drops = _Game_Enemy_makeDropItems.call(this);
        const dropList = this.enemy().dropItems;
        if (dropList && dropList.length > 0) {
            for (let i = 0; i < extraSlots; i++) {
                // ドロップリストからランダムに1つ選ぶ
                const di = dropList[Math.floor(Math.random() * dropList.length)];
                // 確率判定: denominator 値に応じた確率でドロップ
                if (Math.random() * di.denominator < 1) {
                    const item = this.itemObject(di.kind, di.dataId);
                    if (item) drops.push(item);
                }
            }
        }
        return drops;
    };
})();
