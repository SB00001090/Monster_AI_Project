import { useMemo, useState } from "react";
import StableDiffusionUI, { type SDGenerationParams } from "@/components/StableDiffusionUI";
import { trpc } from "@/lib/trpc";
import { toast } from "sonner";
import { useGuest } from "@/contexts/GuestContext";

export function TextToImagePage() {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const { isGuest, consumeImage, canImage, quota } = useGuest();
  const checkpointsQuery = trpc.image.getCheckpoints.useQuery();
  const models = useMemo(() => {
    const checkpoints = checkpointsQuery.data?.checkpoints ?? [];
    if (checkpoints.length === 0) {
      return undefined;
    }
    return checkpoints.map((id) => ({
      id,
      name: id.split(/[/\\]/).pop() ?? id,
      version: checkpointsQuery.data?.active === id ? "active" : "",
    }));
  }, [checkpointsQuery.data]);

  const generateMutation = trpc.image.generateImage.useMutation({
    onError: (error) => toast.error(error.message),
  });

  const handleGenerate = async (params: SDGenerationParams) => {
    let remainingAfter: number | null = null;
    if (isGuest) {
      if (!canImage()) {
        toast.error(`今日圖像額度已用完（${quota.imageLimit} 次）。請明日再試或升級正式版。`);
        return;
      }
      const consumed = consumeImage();
      if (!consumed.ok) {
        toast.error(consumed.message ?? "圖像額度不足");
        return;
      }
      remainingAfter = consumed.remaining;
    }
    const result = await generateMutation.mutateAsync({
      prompt: params.prompt,
      negativePrompt: params.negativePrompt,
      width: params.width,
      height: params.height,
      style: params.modelId,
      checkpoint: params.modelId,
    });
    if (result.imageUrl) {
      setPreviewUrl(result.imageUrl);
    }
    if (result.warning) {
      toast.warning(result.warning);
    }
    toast.success(
      remainingAfter != null
        ? `Image generated（剩餘 ${remainingAfter} 次）`
        : "Image generated",
    );
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-2">
        <h1 className="text-2xl font-bold">Text to Image</h1>
        {isGuest && (
          <p className="text-xs text-cyan-300/90">
            公測圖像額度 {quota.imageRemaining}/{quota.imageLimit}
          </p>
        )}
      </div>
      <StableDiffusionUI
        onGenerate={handleGenerate}
        isLoading={generateMutation.isPending}
        models={models}
      />
      {previewUrl && (
        <div className="rounded-lg border border-border overflow-hidden bg-card">
          <img src={previewUrl} alt="Generated" className="w-full max-h-[70vh] object-contain" />
        </div>
      )}
    </div>
  );
}