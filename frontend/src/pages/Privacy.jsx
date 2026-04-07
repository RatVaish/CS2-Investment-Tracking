import { Link } from 'react-router-dom';

const privacyHtml = `<style>
  [data-custom-class='body'], [data-custom-class='body'] * { background: transparent !important; }
  [data-custom-class='title'], [data-custom-class='title'] * { font-family: Arial !important; font-size: 26px !important; color: #000000 !important; }
  [data-custom-class='subtitle'], [data-custom-class='subtitle'] * { font-family: Arial !important; color: #595959 !important; font-size: 14px !important; }
  [data-custom-class='heading_1'], [data-custom-class='heading_1'] * { font-family: Arial !important; font-size: 19px !important; color: #000000 !important; }
  [data-custom-class='heading_2'], [data-custom-class='heading_2'] * { font-family: Arial !important; font-size: 17px !important; color: #000000 !important; }
  [data-custom-class='body_text'], [data-custom-class='body_text'] * { color: #595959 !important; font-size: 14px !important; font-family: Arial !important; }
  [data-custom-class='link'], [data-custom-class='link'] * { color: #3030F1 !important; font-size: 14px !important; font-family: Arial !important; word-break: break-word !important; }
  ul { list-style-type: square; }
  ul > li > ul { list-style-type: circle; }
  ul > li > ul > li > ul { list-style-type: square; }
  ol li { font-family: Arial; }
  table { width: 100%; border-collapse: collapse; }
  td, th { padding: 8px; }
</style>
<div data-custom-class="body">
<div><strong><span style="font-size: 26px;"><span data-custom-class="title"><h1>PRIVACY POLICY</h1></span></span></strong></div>
<div><span style="color: rgb(127, 127, 127);"><strong><span style="font-size: 15px;"><span data-custom-class="subtitle">Last updated April 07, 2026</span></span></strong></span></div>
<br/>
<div style="line-height: 1.5;"><span style="color: rgb(89, 89, 89); font-size: 15px;"><span data-custom-class="body_text">This Privacy Notice for <strong>Floatbase</strong> ('we', 'us', or 'our'), describes how and why we might access, collect, store, use, and/or share ('process') your personal information when you use our services ('Services'), including when you:</span></span></div>
<ul>
<li data-custom-class="body_text" style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);">Visit our website at <a target="_blank" data-custom-class="link" href="https://floatbase.app">https://floatbase.app</a></span></li>
<li data-custom-class="body_text" style="line-height: 1.5;"><span style="font-size: 15px;">Use Floatbase — a web-based portfolio tracking and investment analytics platform for Counter-Strike 2 skin traders. Users can track their CS2 item investments, monitor real-time prices from Steam, Buff163, and CSFloat, and analyse portfolio performance with profit/loss and ROI calculations. The platform offers a free tier and a paid Pro subscription with enhanced features.</span></li>
<li data-custom-class="body_text" style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);">Engage with us in other related ways, including any marketing or events</span></li>
</ul>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span style="color: rgb(127, 127, 127);"><span data-custom-class="body_text"><strong>Questions or concerns?</strong> Reading this Privacy Notice will help you understand your privacy rights and choices. If you do not agree with our policies and practices, please do not use our Services. If you still have any questions or concerns, please contact us at <a target="_blank" data-custom-class="link" href="mailto:hello@floatbase.app">hello@floatbase.app</a>.</span></span></span></div>
<br/>
<div style="line-height: 1.5;"><strong><span style="font-size: 15px;"><span data-custom-class="heading_1"><h2>SUMMARY OF KEY POINTS</h2></span></span></strong></div>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="body_text"><strong>What personal information do we process?</strong> When you visit, use, or navigate our Services, we may process personal information depending on how you interact with us and the Services, the choices you make, and the products and features you use.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="body_text"><strong>Do we process any sensitive personal information?</strong> We do not process sensitive personal information.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="body_text"><strong>How do we keep your information safe?</strong> We have adequate organisational and technical processes and procedures in place to protect your personal information. However, no electronic transmission over the internet or information storage technology can be guaranteed to be 100% secure.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="body_text"><strong>How do you exercise your rights?</strong> The easiest way to exercise your rights is by visiting <a target="_blank" data-custom-class="link" href="mailto:hello@floatbase.app">hello@floatbase.app</a>, or by contacting us. We will consider and act upon any request in accordance with applicable data protection laws.</span></span></div>
<br/><br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>1. WHAT INFORMATION DO WE COLLECT?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">We collect personal information that you voluntarily provide to us when you register on the Services, express an interest in obtaining information about us or our products and Services, when you participate in activities on the Services, or otherwise when you contact us.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text"><strong>Personal Information Provided by You.</strong> The personal information we collect may include: names, email addresses, usernames, passwords, contact or authentication data, steam id and steam profile data.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="body_text"><strong>Sensitive Information.</strong> We do not process sensitive information.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text"><strong>Payment Data.</strong> We may collect data necessary to process your payment if you choose to make purchases. All payment data is handled and stored by <strong>Stripe</strong>. You may find their privacy notice at: <a target="_blank" data-custom-class="link" href="https://stripe.com/privacy">https://stripe.com/privacy</a>.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text"><strong>Social Media Login Data.</strong> We may provide you with the option to register with us using your existing Google or Steam account. If you choose to register in this way, we will collect certain profile information about you from the social media provider.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><strong><span data-custom-class="heading_2"><h3>Google API</h3></span></strong><span data-custom-class="body_text">Our use of information received from Google APIs will adhere to <a data-custom-class="link" href="https://developers.google.com/terms/api-services-user-data-policy" rel="noopener noreferrer" target="_blank">Google API Services User Data Policy</a>, including the <a data-custom-class="link" href="https://developers.google.com/terms/api-services-user-data-policy#limited-use" rel="noopener noreferrer" target="_blank">Limited Use requirements</a>.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>2. HOW DO WE PROCESS YOUR INFORMATION?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">We process your personal information for a variety of reasons, depending on how you interact with our Services, including: to facilitate account creation and authentication, to deliver and facilitate delivery of services to you, to respond to user inquiries, to send administrative information, to fulfil and manage your orders, to protect our Services, and to identify usage trends.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>3. WHAT LEGAL BASES DO WE RELY ON TO PROCESS YOUR INFORMATION?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">We only process your personal information when we believe it is necessary and we have a valid legal reason to do so under applicable law, like with your consent, to comply with laws, to provide you with services, to protect your rights, or to fulfil our legitimate business interests. For EU/UK users, we rely on: Consent, Performance of a Contract, Legitimate Interests, Legal Obligations, and Vital Interests.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>4. WHEN AND WITH WHOM DO WE SHARE YOUR PERSONAL INFORMATION?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">We may share information in specific situations with the following third parties:</span></span></div>
<ul>
<li data-custom-class="body_text" style="line-height: 1.5;"><span style="font-size: 15px;"><strong>Allow Users to Connect to Their Third-Party Accounts:</strong> Google account and Steam account</span></li>
<li data-custom-class="body_text" style="line-height: 1.5;"><span style="font-size: 15px;"><strong>Invoice and Billing:</strong> Stripe</span></li>
<li data-custom-class="body_text" style="line-height: 1.5;"><span style="font-size: 15px;"><strong>User Account Registration and Authentication:</strong> Google Sign-In and Steam OpenID</span></li>
<li data-custom-class="body_text" style="line-height: 1.5;"><span style="font-size: 15px;"><strong>Business Transfers:</strong> We may share or transfer your information in connection with any merger, sale of company assets, financing, or acquisition.</span></li>
</ul>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>5. DO WE USE COOKIES AND OTHER TRACKING TECHNOLOGIES?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">We may use cookies and similar tracking technologies to gather information when you interact with our Services. Specific information about how we use such technologies is set out in our Cookie Policy.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>6. HOW DO WE HANDLE YOUR SOCIAL LOGINS?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">Our Services offer you the ability to register and log in using your Google or Steam account. Where you choose to do this, we will receive certain profile information about you from your social media provider, such as your name and email address. We will use this information only for the purposes described in this Privacy Notice.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>7. HOW LONG DO WE KEEP YOUR INFORMATION?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">We will only keep your personal information for as long as it is necessary for the purposes set out in this Privacy Notice. No purpose in this notice will require us keeping your personal information for longer than the period of time in which users have an account with us.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>8. HOW DO WE KEEP YOUR INFORMATION SAFE?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">We have implemented appropriate and reasonable technical and organisational security measures designed to protect the security of any personal information we process. However, no electronic transmission over the Internet or information storage technology can be guaranteed to be 100% secure.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>9. DO WE COLLECT INFORMATION FROM MINORS?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">We do not knowingly collect, solicit data from, or market to children under 18 years of age. By using the Services, you represent that you are at least 18. If you become aware of any data we may have collected from children under age 18, please contact us at <a target="_blank" data-custom-class="link" href="mailto:hello@floatbase.app">hello@floatbase.app</a>.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>10. WHAT ARE YOUR PRIVACY RIGHTS?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">Depending on where you are located, you may have rights including: the right to access and obtain a copy of your personal information, the right to request rectification or erasure, the right to restrict processing, and the right to data portability. You can make such a request by contacting us at <a target="_blank" data-custom-class="link" href="mailto:hello@floatbase.app">hello@floatbase.app</a>.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">If you are located in the EEA or UK and you believe we are unlawfully processing your personal information, you have the right to complain to your <a data-custom-class="link" href="https://ec.europa.eu/justice/data-protection/bodies/authorities/index_en.htm" rel="noopener noreferrer" target="_blank">Member State data protection authority</a> or <a data-custom-class="link" href="https://ico.org.uk/make-a-complaint/data-protection-complaints/data-protection-complaints/" rel="noopener noreferrer" target="_blank">UK data protection authority</a>.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><strong><span data-custom-class="heading_2"><h3>Account Information</h3></span></strong></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">If you would like to review or change the information in your account or terminate your account, you can log in to your account settings, contact us using the contact information provided, or email us at <a target="_blank" data-custom-class="link" href="mailto:hello@floatbase.app">hello@floatbase.app</a> to request account deletion.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>11. CONTROLS FOR DO-NOT-TRACK FEATURES</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">Most web browsers and some mobile operating systems include a Do-Not-Track ('DNT') feature. As no uniform technology standard for recognising and implementing DNT signals has been finalised, we do not currently respond to DNT browser signals.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>12. DO UNITED STATES RESIDENTS HAVE SPECIFIC PRIVACY RIGHTS?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">If you are a resident of California, Colorado, Connecticut, or other applicable US states, you may have the right to request access to and receive details about the personal information we maintain about you, correct inaccuracies, get a copy of, or delete your personal information. To exercise these rights, please contact us at <a target="_blank" data-custom-class="link" href="mailto:hello@floatbase.app">hello@floatbase.app</a>.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>13. DO WE MAKE UPDATES TO THIS NOTICE?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">We may update this Privacy Notice from time to time. The updated version will be indicated by an updated 'Revised' date at the top of this Privacy Notice. We encourage you to review this Privacy Notice frequently.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>14. HOW CAN YOU CONTACT US ABOUT THIS NOTICE?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">If you have questions or comments about this notice, you may email us at <a target="_blank" data-custom-class="link" href="mailto:hello@floatbase.app">hello@floatbase.app</a> or contact us by post at: London, United Kingdom.</span></span></div>
<br/>
<div style="line-height: 1.5;"><span style="font-size: 15px;"><span data-custom-class="heading_1"><strong><h2>15. HOW CAN YOU REVIEW, UPDATE, OR DELETE THE DATA WE COLLECT FROM YOU?</h2></strong></span></span></div>
<div style="line-height: 1.5;"><span style="font-size: 15px; color: rgb(89, 89, 89);"><span data-custom-class="body_text">Based on the applicable laws of your country or state of residence, you may have the right to request access to the personal information we collect from you, correct inaccuracies, or delete your personal information. To request to review, update, or delete your personal information, please visit: <a target="_blank" data-custom-class="link" href="mailto:hello@floatbase.app">hello@floatbase.app</a>.</span></span></div>
</div>`;

function Privacy() {
  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#111827', padding: '40px 24px' }}>
      <div style={{ maxWidth: '900px', margin: '0 auto' }}>
        <a href="/" style={{ color: '#60a5fa', textDecoration: 'none', fontSize: '14px' }}>
          ← Back to Floatbase
        </a>
        <div style={{
          marginTop: '24px',
          background: '#ffffff',
          borderRadius: '12px',
          padding: '48px',
          boxShadow: '0 4px 24px rgba(0,0,0,0.4)'
        }}>
          <div dangerouslySetInnerHTML={{ __html: privacyHtml }} />
        </div>
        <div style={{ textAlign: 'center', marginTop: '24px', color: '#6b7280', fontSize: '12px' }}>
          © 2026 Floatbase. All rights reserved.
        </div>
      </div>
    </div>
  );
}

export default Privacy;
