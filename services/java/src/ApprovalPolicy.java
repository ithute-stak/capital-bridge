import java.util.Locale;

/** Deterministic approval policy; never authorises a user or posts a journal. */
public final class ApprovalPolicy {
    private ApprovalPolicy() {}
    public static String recommendation(long amountMinor, long dualReviewThresholdMinor) {
        if (amountMinor < 0 || dualReviewThresholdMinor < 0)
            throw new IllegalArgumentException("Amounts must be nonnegative minor units");
        return amountMinor >= dualReviewThresholdMinor ? "DUAL_REVIEW" : "STANDARD_REVIEW";
    }
    public static void main(String[] args) {
        if (args.length != 2) throw new IllegalArgumentException("Expected amount and threshold");
        System.out.println(recommendation(Long.parseLong(args[0]), Long.parseLong(args[1])));
    }
}
