"use client";

import { BackButton } from "@/components/ui/BackButton";
import { Screen } from "@/components/ui/Screen";
import { ErrorState, Skeleton } from "@/components/ui/States";
import { useSession } from "@/core/session/SessionProvider";
import { useWorkerReviews } from "@/features/reviews/hooks";
import { ReviewList } from "@/features/reviews/ReviewList";

/** The worker's own reviews: reply once to each, or report one to the Maritcho team. */
export function WorkerReviewsScreen() {
  const { user } = useSession();
  const reviews = useWorkerReviews(user?.id);

  return (
    <Screen glow="worker">
      <div className="topbar">
        <BackButton fallbackHref="/worker/work?tab=done" />
        <div className="topbar__text">
          <h1 className="title">What clients say</h1>
          <div className="meta">Clients see these on your profile</div>
        </div>
      </div>
      {reviews.isError ? (
        <ErrorState message={reviews.error.message} onRetry={() => void reviews.refetch()} />
      ) : reviews.data && user ? (
        <ReviewList
          page={reviews.data}
          title="Your reviews"
          ownerWorkerId={user.id}
          emptyText="No reviews yet. After each signed-off job, the client has 14 days to review you."
        />
      ) : (
        <Skeleton height={160} count={2} />
      )}
    </Screen>
  );
}
