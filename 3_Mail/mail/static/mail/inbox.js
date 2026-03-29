document.addEventListener('DOMContentLoaded', function() {

  // Use buttons to toggle between views
  document.querySelector('#inbox').addEventListener('click', () => load_mailbox('inbox'));
  document.querySelector('#sent').addEventListener('click', () => load_mailbox('sent'));
  document.querySelector('#archived').addEventListener('click', () => load_mailbox('archive'));
  document.querySelector('#compose').addEventListener('click', () => compose_email());
  const body = document.querySelector(".container");
  const view_email = document.createElement("div");
  view_email.id = "view-single-email";
  body.appendChild(view_email);

  // By default, load the inbox
  load_mailbox('inbox');

  // Send Email Form
  document.querySelector('form').onsubmit = async (e) => {
    e.preventDefault();

    recipients = document.querySelector('#compose-recipients').value;
    subject = document.querySelector('#compose-subject').value;
    mailbody = document.querySelector('#compose-body').value;
    await send_email(recipients, subject, mailbody);
  }
});

function compose_email(recipient="", subject="", body="") {

  // Show compose view and hide other views
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#view-single-email').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'block';

  // Clear out composition fields
  document.querySelector('#compose-recipients').value = recipient;
  document.querySelector('#compose-subject').value = subject;
  document.querySelector('#compose-body').value = body;
}

// Mailbox overview
async function load_mailbox(mailbox) {
  
  // Show the mailbox and hide other views
  document.querySelector('#emails-view').style.display = 'block';
  document.querySelector('#compose-view').style.display = 'none';
  document.querySelector('#view-single-email').style.display = 'none';

  // Show the mailbox name
  document.querySelector('#emails-view').innerHTML = `<h3>${mailbox.charAt(0).toUpperCase() + mailbox.slice(1)}</h3>`;

  const maillist = await get_mailbox(mailbox);
  maillist.forEach((element) => {
    const div = document.createElement("div");
    div.className = "email-card";
    if (element.read === true){
      div.style = "border: 1px solid gray; border-radius: 8px; padding: 4px; margin: 4px; width: 50%; background-color: lightgray; font-style: italic;";
    }
    else {
      div.style = "border: 1px solid gray; border-radius: 8px; padding: 4px; margin: 4px; width: 50%; background-color: white";
    }

    const from = document.createElement("div");
    from.className = "from"
    from.innerText = `From: ${element.sender}`;
    div.appendChild(from);



    const subj = document.createElement("span");
    subj.className = "subject";
    subj.innerHTML = `<strong>${element.subject}</strong>`
    div.appendChild(subj);

    const textbody = document.createElement("div");
    textbody.innerText = element.body.slice(0,20) + " (...)";
    div.appendChild(textbody);
    div.onclick = async () => await display_detail_mail(element)
    
    document.querySelector("#emails-view").appendChild(div);
  });
}

function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
      cookie = cookie.trim();
      if (cookie.startsWith(name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
const csrftoken = getCookie('csrftoken');

async function send_email(recipients, subject, mailbody) {
  try {
    const response = await fetch("/emails", {
      method: "POST",
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
      },
      body: JSON.stringify({ recipients, subject, body: mailbody }),
    });

    const result = await response.json();

    if (!response.ok) {
      const errorMessage = result.error || result.message || 'Unable to send email.';
      alert(`Send failed: ${errorMessage}`);
      return;
    }

    // On success clear the form and go to sent mailbox
    document.querySelector('#compose-recipients').value = '';
    document.querySelector('#compose-subject').value = '';
    document.querySelector('#compose-body').value = '';
    load_mailbox('sent');
  } catch (error) {
    console.error(error.message);
    alert('Unexpected error while sending email. Please try again.');
  }
}


async function get_mailbox(mailbox) {
  try {
    const response = await fetch(`/emails/${mailbox}`, {
      method: "GET",
      headers: {
        'X-CSRFToken': csrftoken,
      },
    });
    if (response.ok) {
      const inbox = await response.json();
      return inbox;
    } else {
      console.log("Got no successful response from server");
    }
  } catch (error) {
    console.log("Error loading mailbox:", error);
  }
}


async function change_archive_status(mail){
  try {
      const response = await fetch(`/emails/${mail.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
      },
      body: JSON.stringify({
          archived: !mail.archived
      }),
    });
    console.log(`Marked Email archived=${!mail.archived}!`);
  } catch (error) {
    console.log("Error trying to mark Email as (un)archived")
    console.error(error.message);
  }

  load_mailbox('inbox');
}

async function change_read_status(mail){
  try {
      const response = await fetch(`/emails/${mail.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken,
      },
      body: JSON.stringify({
          read: !mail.read
      }),
    });
    console.log(`Marked Email read=${!mail.read}!`);
  } catch (error) {
    console.log("Error trying to mark Email as read")
    console.error(error.message);
  }
}


async function display_detail_mail(mail, own_email=false) {

  // Set containers
  document.querySelector('#emails-view').style.display = 'none';
  document.querySelector('#compose-view').style.display = 'none';
  mailview = document.querySelector('#view-single-email');
  mailview.style.display = 'block';

  // Create Mailview container
  const div = document.createElement("div");
  
  div.className = "detail-mail";
  
  // Add Archive buttons
  if (!own_email) {
    const archivebutton = document.createElement('button');
    archivebutton.classList.add("btn", "btn-primary", "m-1");
    if (mail.archived) archivebutton.innerHTML = 'Unarchive Email';
    else archivebutton.innerHTML = 'Archive Email';

    archivebutton.addEventListener('click', function() {
        change_archive_status(mail);
    });
    div.append(archivebutton);
  }

  // Add reply button
  const replybutton = document.createElement('button');
  replybutton.classList.add("btn", "btn-primary", "m-1")
  replybutton.innerHTML = 'Reply';
  
  const replysubject = mail.subject.startsWith("Re:") ? mail.subject : `Re: ${mail.subject}`;
  replybutton.addEventListener('click', () => compose_email(recipient=mail.sender, subject=replysubject, body=`\n------------\nOn ${mail.timestamp}, ${mail.sender} wrote:\n ${mail.body}`));
  div.append(replybutton);

  // Add message details
  const from = document.createElement("div");
  from.className = "from"
  from.innerText = `From ${mail.sender}`;
  div.appendChild(from);

  const time = document.createElement("div");
  time.innerText = `${mail.timestamp}`;
  div.appendChild(time);
  
  const subjectdiv = document.createElement("div");
  subjectdiv.classList.add("subject", "mt-3");
  subjectdiv.innerHTML = `<strong>Subject: ${mail.subject}`
  div.appendChild(subjectdiv);

  const textbody = document.createElement("div");
  textbody.innerText = mail.body;
  div.appendChild(textbody);
  
  mailview.innerHTML = "";
  mailview.appendChild(div);

  if (!mail.read) {
    change_read_status(mail);
  }
}
