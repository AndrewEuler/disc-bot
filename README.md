# Discord bot with DB and shop

When you turn on the bot, the database is created automatically, if there has not been one yet

## Main functions

It has the following set of functions:

1. `create-channel` - Creates a text channel with the specified name.
2. `my-role` - Gives you a role on the server if you have the necessary rights for it.
3. `roll` - Throws a 6-sided die n-times.
4. `help` - Shows a list of all commands.
5. `setdelay` - Sets the «slowmode» on the channel.
6. `purge` - Clears the N-th number of messages.
7. `status` - Shows your status on the server based on the data in the database.
8. `timeout` - Throws the selected participant into timeout.
9. `change-balance` - Updates the participant's balance in DB.
10. `create_shop` - Creates a drop-down list of the store.

When adding a new user to the discord channel, the bot welcomes him and adds the role assigned to him by default.
The `error_handler` command is handles errors.

## Shop

There are 3 lots in the store: Buy a new role, connect a participant for up to 1 hour, open a case. 
When choosing to purchase a role or mute a participant, you are given the appropriate role coupon, which gives you the opportunity to use previously unavailable commands **«timeout»** and **«my-role»**.
When opening the case, it randomly gives out what is inside. 
When buying a particular lot, a certain amount is withdrawn from the balance, which is set in variables.

All necessary parameters are changed in the «.env» file. See the examples in the .env.template file.

## A little more fun

Additional functions:

1. When using **@everyone**, the corresponding image is sent from the images folder.
2. When chatting, he randomly sends a picture.

