
/*:
 * @target MZ
 * @plugindesc ゲーム進行速度を10倍にする（スイッチでON/OFF可能）プラグイン v1.3 by 鈴木
 * @author 鈴木
 *
 * @param SpeedUpSwitchId
 * @text 高速化スイッチID
 * @type switch
 * @default 1
 * @desc このスイッチがONのとき、ゲーム速度を10倍にします。
 *
 * @help
 * ゲーム進行速度を10倍にします。
 * 指定したスイッチがONのときのみ有効になります。
 *
 * 使用方法:
 * - プラグインをプロジェクトの js/plugins に配置
 * - プラグイン管理で有効化
 * - パラメータでスイッチIDを指定
 * - ゲーム内でそのスイッチをONにすると高速化されます
 *
 * 注意:
 * 一部のイベントやアニメーションが高速で実行されるため、見えにくくなる場合があります。
 */

(() => {
    const pluginName = "GameSpeedX10_LoopSwitch";
    const parameters = PluginManager.parameters(pluginName);
    const speedSwitchId = Number(parameters["SpeedUpSwitchId"] || 1);

    const originalUpdateMain = SceneManager.updateMain;

    SceneManager.updateMain = function() {
        if ($gameSwitches && $gameSwitches.value(speedSwitchId)) {
            for (let i = 0; i < 10; i++) {
                originalUpdateMain.call(this);
            }
        } else {
            originalUpdateMain.call(this);
        }
    };
})();
