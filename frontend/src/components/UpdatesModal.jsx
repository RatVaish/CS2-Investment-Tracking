import { useState } from "react";
import { markUpdatesRead } from "../api/updates";

export default function UpdatesModal({ updates, onClose }) {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isClosing, setIsClosing] = useState(false);

  if (!updates || updates.length === 0) return null;

  const currentUpdate = updates[currentIndex];
  const isFirst = currentIndex === 0;
  const isLast = currentIndex === updates.length - 1;

  const handlePrevious = () => {
    if (!isFirst) {
      setCurrentIndex(currentIndex - 1);
    }
  };

  const handleNext = () => {
    if (!isLast) {
      setCurrentIndex(currentIndex + 1);
    }
  };

  const handleClose = async () => {
    setIsClosing(true);
    try {
      // Mark all updates as read
      const updateIds = updates.map((u) => u.id);
      await markUpdatesRead(updateIds);
      onClose();
    } catch (error) {
      console.error("Failed to mark updates as read:", error);
      // Still close the modal even if marking fails
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-60 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 rounded-2xl border border-gray-700 w-full max-w-xl overflow-hidden">
        {/* Header */}
        <div className="px-6 py-5 border-b border-gray-700 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-medium text-white">
              What's new in Floatbase
            </h2>
            <p className="text-sm text-gray-400 mt-1">
              {updates.length === 1
                ? "1 update since your last visit"
                : `${updates.length} updates since your last visit`}
            </p>
          </div>
          <button
            onClick={handleClose}
            disabled={isClosing}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-gray-400 hover:text-white hover:bg-gray-800 transition-colors"
            aria-label="Close"
          >
            <svg
              className="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-8">
          {/* Icon/Image Area */}
          <div className="bg-cyan-900 bg-opacity-20 rounded-xl p-12 text-center mb-6">
            {currentUpdate.image_url ? (
              <img
                src={currentUpdate.image_url}
                alt={currentUpdate.title}
                className="max-w-full h-auto mx-auto"
              />
            ) : (
              <svg
                className="w-12 h-12 mx-auto text-cyan-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
            )}
          </div>

          {/* Update Content */}
          <div className="text-center">
            <h3 className="text-base font-medium text-white mb-2">
              {currentUpdate.title}
            </h3>
            <p className="text-sm text-gray-400 leading-relaxed mb-3">
              {currentUpdate.description}
            </p>
            <span className="text-xs text-gray-500">
              Added {new Date(currentUpdate.created_at).toLocaleDateString()}
            </span>
          </div>
        </div>

        {/* Navigation */}
        <div className="px-6 pb-6 flex items-center justify-between">
          <button
            onClick={handlePrevious}
            disabled={isFirst}
            className="px-4 py-2 text-sm text-gray-400 hover:text-white disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
          >
            <svg
              className="w-4 h-4 inline-block mr-1 align-text-bottom"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M15 19l-7-7 7-7"
              />
            </svg>
            Previous
          </button>

          {/* Dots */}
          <div className="flex gap-1.5">
            {updates.map((_, idx) => (
              <div
                key={idx}
                className={`w-2 h-2 rounded-full ${
                  idx === currentIndex ? "bg-cyan-400" : "bg-gray-700"
                }`}
              />
            ))}
          </div>

          <button
            onClick={isLast ? handleClose : handleNext}
            disabled={isClosing}
            className="px-4 py-2 text-sm font-medium text-white hover:text-cyan-400 disabled:opacity-30 transition-colors"
          >
            {isLast ? "Got it" : "Next"}
            {!isLast && (
              <svg
                className="w-4 h-4 inline-block ml-1 align-text-bottom"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            )}
          </button>
        </div>

        {/* Footer Button (on last slide) */}
        {isLast && (
          <div className="px-6 pb-6 pt-0">
            <button
              onClick={handleClose}
              disabled={isClosing}
              className="w-full py-2.5 text-sm font-medium bg-cyan-600 hover:bg-cyan-700 disabled:bg-gray-700 text-white rounded-lg transition-colors"
            >
              {isClosing ? "Closing..." : "Got it"}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
