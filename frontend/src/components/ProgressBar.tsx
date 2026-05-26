interface Props {
  percent: number
}

export default function ProgressBar({ percent }: Props) {
  const clampedPercent = Math.min(100, Math.max(0, percent))

  return (
    <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
      <div
        className="bg-green-500 h-full rounded-full transition-all duration-300"
        style={{ width: `${clampedPercent}%` }}
      />
    </div>
  )
}
