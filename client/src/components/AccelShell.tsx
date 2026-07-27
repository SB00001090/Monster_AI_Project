/**
 * 加速包殼：手勢層、自動更新、緊急回報
 * 開發者：suckbob | 發行商：Monster_Ai_hk
 */
import { useCallback, useEffect, useState } from "react";
import GestureLayer from "@/components/gestures/GestureLayer";
import InstantFeedbackModal from "@/components/feedback/InstantFeedbackModal";
import BlueRoseUnlockAnimation from "@/components/themes/BlueRoseUnlockAnimation";
import { useAutoUpdate } from "@/hooks/useAutoUpdate";
import { useUiTheme } from "@/contexts/UiThemeContext";
import { useGestures } from "@/contexts/GestureContext";

export default function AccelShell() {
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [roseAnim, setRoseAnim] = useState(false);
  const { unlockHidden, hiddenUnlocked } = useUiTheme();
  const { setInputFocused } = useGestures();

  useAutoUpdate(true);

  useEffect(() => {
    const onEmergency = () => setFeedbackOpen(true);
    window.addEventListener("monster:emergency-feedback", onEmergency);
    return () => window.removeEventListener("monster:emergency-feedback", onEmergency);
  }, []);

  // 輸入框聚焦 → 暫停衝突手勢
  useEffect(() => {
    const focusIn = (e: FocusEvent) => {
      const t = e.target as HTMLElement | null;
      if (!t) return;
      const tag = t.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || t.isContentEditable) {
        setInputFocused(true);
      }
    };
    const focusOut = () => setInputFocused(false);
    window.addEventListener("focusin", focusIn);
    window.addEventListener("focusout", focusOut);
    return () => {
      window.removeEventListener("focusin", focusIn);
      window.removeEventListener("focusout", focusOut);
    };
  }, [setInputFocused]);

  // 藍玫瑰解鎖事件（由設定頁觸發）
  useEffect(() => {
    const onUnlock = () => {
      if (hiddenUnlocked) return;
      setRoseAnim(true);
    };
    window.addEventListener("monster:unlock-blue-rose", onUnlock);
    return () => window.removeEventListener("monster:unlock-blue-rose", onUnlock);
  }, [hiddenUnlocked]);

  const onRoseDone = useCallback(() => {
    setRoseAnim(false);
    unlockHidden();
  }, [unlockHidden]);

  return (
    <>
      <GestureLayer />
      <InstantFeedbackModal open={feedbackOpen} onClose={() => setFeedbackOpen(false)} />
      <BlueRoseUnlockAnimation show={roseAnim} onDone={onRoseDone} />
    </>
  );
}
