"use client";

import { ReceiptText } from "lucide-react";
import { api, PAYMENT_NOTICE, post } from "./api";
import { BusyButton, ErrorPanel, useAction, useData } from "./ui";
import { useWorkspace } from "./workspace";
import type { Integrations, Invoice } from "./types";

export const SANDBOX_NOTICE =
  "PAYPAL SANDBOX — TEST TRANSACTION — NO REAL MONEY";

export function PaymentModeNotice({ invoice }: { invoice?: Invoice | null }) {
  const configuration = useData<Integrations>("/integrations");
  const sandbox = invoice
    ? invoice.provider === "paypal_sandbox"
    : configuration.data?.payment_provider === "paypal_sandbox";
  return (
    <div className="alert warning">
      {!invoice && configuration.loading ? (
        "Loading payment provider status…"
      ) : !invoice && configuration.error ? (
        "Payment provider status unavailable. Check Demo & integrations before taking a payment action."
      ) : (
        <>
          <span className="provider-badge">
            {sandbox ? "PayPal Sandbox (test funds)" : "Mock provider"}
          </span>{" "}
          {sandbox ? SANDBOX_NOTICE : PAYMENT_NOTICE}
          {!sandbox && (
            <small className="payment-clarification">
              SIMULATED PAYMENT — NO PAYPAL TRANSACTION
            </small>
          )}
        </>
      )}
    </div>
  );
}

export function CreateInvoiceAction({
  royaltyId,
  disabled,
}: {
  royaltyId: string;
  disabled: boolean;
}) {
  const configuration = useData<Integrations>("/integrations");
  const sandbox = configuration.data?.payment_provider === "paypal_sandbox";
  const { busy, error, run } = useAction();
  const { notify } = useWorkspace();
  return (
    <>
      <BusyButton
        busy={busy}
        disabled={
          disabled || configuration.loading || Boolean(configuration.error)
        }
        onClick={() =>
          void run(async () => {
            let confirmation = {};
            if (sandbox) {
              const preview = await api<{
                amount: string;
                currency: string;
                sandbox_payload: {
                  merchant_email: string;
                  buyer_email: string;
                };
              }>(`/royalties/${royaltyId}/invoice-preview`);
              const buyer = preview.sandbox_payload.buyer_email;
              if (
                !window.confirm(
                  `Create one PayPal SANDBOX draft?\nCase: ${royaltyId}\nIssuer: ${preview.sandbox_payload.merchant_email}\nBuyer: ${buyer}\nAmount: ${preview.amount} ${preview.currency}\nThis does not send the invoice or move money.`,
                )
              )
                return;
              confirmation = {
                confirm_sandbox: true,
                expected_amount: preview.amount,
                expected_currency: preview.currency,
                expected_recipient: buyer,
              };
            }
            const invoice = await post<Invoice>(
              `/royalties/${royaltyId}/invoice`,
              confirmation,
            );
            notify(
              invoice.provider === "paypal_sandbox"
                ? `Actual Sandbox draft ${invoice.provider_id} recorded. Sending is a separate action.`
                : "Simulated invoice ready. No funds were transferred.",
            );
          })
        }
      >
        <ReceiptText size={15} />
        {sandbox
          ? "Create / open PayPal Sandbox draft"
          : "Create / open simulated invoice"}
      </BusyButton>
      {sandbox && !configuration.data?.paypal_configuration?.drafts_enabled && (
        <p className="small">
          Sandbox draft writes are disabled until the owner explicitly enables
          them. No automatic invoice is created.
        </p>
      )}
      {error && <ErrorPanel message={error} />}
      {configuration.error && (
        <ErrorPanel message={configuration.error} retry={configuration.retry} />
      )}
    </>
  );
}
